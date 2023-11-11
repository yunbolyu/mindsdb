from copy import deepcopy

from mindsdb_sql import parse_sql
from mindsdb_sql.parser.ast import (
    BinaryOperation,
    Identifier,
    Constant
)

from mindsdb.api.mysql.mysql_proxy.datahub.datanodes.datanode import DataNode
from mindsdb.api.mysql.mysql_proxy.datahub.classes.tables_row import TablesRow
from mindsdb.api.mysql.mysql_proxy.classes.sql_query import SQLQuery
from mindsdb.api.mysql.mysql_proxy.utilities.sql import query_df
from mindsdb.interfaces.query_context.context_controller import query_context_controller


class ProjectDataNode(DataNode):
    type = 'project'

    def __init__(self, project, integration_controller, information_schema):
        self.project = project
        self.integration_controller = integration_controller
        self.information_schema = information_schema

    def get_type(self):
        return self.type

    def get_tables(self):
        tables = self.project.get_tables()
        table_types = {
            'table': 'BASE TABLE',
            'model': 'MODEL',
            'view': 'VIEW'
        }
        tables = [
            {
                'TABLE_NAME': key,
                'TABLE_TYPE': table_types.get(val['type'])
            }
            for key, val in tables.items()
        ]
        result = [TablesRow.from_dict(row) for row in tables]
        return result

    def has_table(self, table_name):
        tables = self.project.get_tables()
        return table_name in tables

    def get_table_columns(self, table_name):
        return self.project.get_columns(table_name)

    def predict(self, model_name: str, data, version=None, params=None):
        model_metadata = self.project.get_model(model_name)
        if model_metadata is None:
            raise Exception(f"Can't find model '{model_name}'")
        model_metadata = model_metadata['metadata']
        if model_metadata['update_status'] == 'available':
            raise Exception(f"model '{model_name}' is obsolete and needs to be updated. Run 'RETRAIN {model_name};'")
        handler = self.integration_controller.get_handler(model_metadata['engine_name'])
        return handler.predict(model_name, data, project_name=self.project.name, version=version, params=params)

    def query(self, query=None, native_query=None, session=None):
        if query is None and native_query is not None:
            query = parse_sql(native_query, dialect='mindsdb')

        # region is it query to 'models' or 'models_versions'?
        query_table = query.from_table.parts[0]
        # region FIXME temporary fix to not broke queries to 'mindsdb.models'. Can be deleted it after 1.12.2022
        if query_table == 'predictors':
            query.from_table.parts[0] = 'models'
            query_table = 'models'
        # endregion
        if query_table in ('models', 'models_versions', 'jobs', 'jobs_history', 'mdb_triggers', 'chatbots', 'skills', 'agents'):
            new_query = deepcopy(query)
            project_filter = BinaryOperation('=', args=[
                Identifier('project'),
                Constant(self.project.name)
            ])
            if new_query.where is None:
                new_query.where = project_filter
            else:
                new_query.where = BinaryOperation('and', args=[
                    new_query.where,
                    project_filter
                ])
            data, columns_info = self.information_schema.query(new_query)
            return data, columns_info
        # endregion

        # region query to views
        view_meta = self.project.query_view(query)

        query_context_controller.set_context('view', view_meta['id'])

        try:
            sqlquery = SQLQuery(
                view_meta['query_ast'],
                session=session
            )
            result = sqlquery.fetch(view='dataframe')

        finally:
            query_context_controller.release_context('view', view_meta['id'])

        if result['success'] is False:
            raise Exception(f"Cant execute view query: {view_meta['query_ast']}")
        df = result['result']

        df = query_df(df, query)

        columns_info = [
            {
                'name': k,
                'type': v
            }
            for k, v in df.dtypes.items()
        ]

        return df.to_dict(orient='records'), columns_info
        # endregion
