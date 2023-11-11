from functools import partial

import pandas as pd
from mindsdb_sql.parser.ast import BinaryOperation, Constant, Identifier, Select
from mindsdb_sql.parser.ast.base import ASTNode

from mindsdb.api.mysql.mysql_proxy.classes.sql_query import get_all_tables
from mindsdb.api.mysql.mysql_proxy.datahub.classes.tables_row import (
    TABLES_ROW_TYPE,
    TablesRow,
)
from mindsdb.api.mysql.mysql_proxy.datahub.datanodes.datanode import DataNode
from mindsdb.api.mysql.mysql_proxy.datahub.datanodes.integration_datanode import (
    IntegrationDataNode,
)
from mindsdb.api.mysql.mysql_proxy.datahub.datanodes.project_datanode import (
    ProjectDataNode,
)
from mindsdb.api.mysql.mysql_proxy.utilities import exceptions as exc
from mindsdb.api.mysql.mysql_proxy.utilities.sql import query_df
from mindsdb.interfaces.agents.agents_controller import AgentsController
from mindsdb.interfaces.database.projects import ProjectController
from mindsdb.interfaces.jobs.jobs_controller import JobsController
from mindsdb.interfaces.skills.skills_controller import SkillsController


class InformationSchemaDataNode(DataNode):
    type = "INFORMATION_SCHEMA"

    information_schema = {
        "SCHEMATA": [
            "CATALOG_NAME",
            "SCHEMA_NAME",
            "DEFAULT_CHARACTER_SET_NAME",
            "DEFAULT_COLLATION_NAME",
            "SQL_PATH",
        ],
        "TABLES": [
            "TABLE_CATALOG",
            "TABLE_SCHEMA",
            "TABLE_NAME",
            "TABLE_TYPE",
            "ENGINE",
            "VERSION",
            "ROW_FORMAT",
            "TABLE_ROWS",
            "AVG_ROW_LENGTH",
            "DATA_LENGTH",
            "MAX_DATA_LENGTH",
            "INDEX_LENGTH",
            "DATA_FREE",
            "AUTO_INCREMENT",
            "CREATE_TIME",
            "UPDATE_TIME",
            "CHECK_TIME",
            "TABLE_COLLATION",
            "CHECKSUM",
            "CREATE_OPTIONS",
            "TABLE_COMMENT",
        ],
        "COLUMNS": [
            "TABLE_CATALOG",
            "TABLE_SCHEMA",
            "TABLE_NAME",
            "COLUMN_NAME",
            "ORDINAL_POSITION",
            "COLUMN_DEFAULT",
            "IS_NULLABLE",
            "DATA_TYPE",
            "CHARACTER_MAXIMUM_LENGTH",
            "CHARACTER_OCTET_LENGTH",
            "NUMERIC_PRECISION",
            "NUMERIC_SCALE",
            "DATETIME_PRECISION",
            "CHARACTER_SET_NAME",
            "COLLATION_NAME",
            "COLUMN_TYPE",
            "COLUMN_KEY",
            "EXTRA",
            "PRIVILEGES",
            "COLUMN_COMMENT",
            "GENERATION_EXPRESSION",
        ],
        "EVENTS": [
            "EVENT_CATALOG",
            "EVENT_SCHEMA",
            "EVENT_NAME",
            "DEFINER",
            "TIME_ZONE",
            "EVENT_BODY",
            "EVENT_DEFINITION",
            "EVENT_TYPE",
            "EXECUTE_AT",
            "INTERVAL_VALUE",
            "INTERVAL_FIELD",
            "SQL_MODE",
            "STARTS",
            "ENDS",
            "STATUS",
            "ON_COMPLETION",
            "CREATED",
            "LAST_ALTERED",
            "LAST_EXECUTED",
            "EVENT_COMMENT",
            "ORIGINATOR",
            "CHARACTER_SET_CLIENT",
            "COLLATION_CONNECTION",
            "DATABASE_COLLATION",
        ],
        "ROUTINES": [
            "SPECIFIC_NAME",
            "ROUTINE_CATALOG",
            "ROUTINE_SCHEMA",
            "ROUTINE_NAME",
            "ROUTINE_TYPE",
            "DATA_TYPE",
            "CHARACTER_MAXIMUM_LENGTH",
            "CHARACTER_OCTET_LENGTH",
            "NUMERIC_PRECISION",
            "NUMERIC_SCALE",
            "DATETIME_PRECISION",
            "CHARACTER_SET_NAME",
            "COLLATION_NAME",
            "DTD_IDENTIFIER",
            "ROUTINE_BODY",
            "ROUTINE_DEFINITION",
            "EXTERNAL_NAME",
            "EXTERNAL_LANGUAGE",
            "PARAMETER_STYLE",
            "IS_DETERMINISTIC",
            "SQL_DATA_ACCESS",
            "SQL_PATH",
            "SECURITY_TYPE",
            "CREATED",
            "LAST_ALTERED",
            "SQL_MODE",
            "ROUTINE_COMMENT",
            "DEFINER",
            "CHARACTER_SET_CLIENT",
            "COLLATION_CONNECTION",
            "DATABASE_COLLATION",
        ],
        "TRIGGERS": [
            "TRIGGER_CATALOG",
            "TRIGGER_SCHEMA",
            "TRIGGER_NAME",
            "EVENT_MANIPULATION",
            "EVENT_OBJECT_CATALOG",
            "EVENT_OBJECT_SCHEMA",
            "EVENT_OBJECT_TABLE",
            "ACTION_ORDER",
            "ACTION_CONDITION",
            "ACTION_STATEMENT",
            "ACTION_ORIENTATION",
            "ACTION_TIMING",
            "ACTION_REFERENCE_OLD_TABLE",
            "ACTION_REFERENCE_NEW_TABLE",
            "ACTION_REFERENCE_OLD_ROW",
            "ACTION_REFERENCE_NEW_ROW",
            "CREATED",
            "SQL_MODE",
            "DEFINER",
            "CHARACTER_SET_CLIENT",
            "COLLATION_CONNECTION",
            "DATABASE_COLLATION",
        ],
        "PLUGINS": [
            "PLUGIN_NAME",
            "PLUGIN_VERSION",
            "PLUGIN_STATUS",
            "PLUGIN_TYPE",
            "PLUGIN_TYPE_VERSION",
            "PLUGIN_LIBRARY",
            "PLUGIN_LIBRARY_VERSION",
            "PLUGIN_AUTHOR",
            "PLUGIN_DESCRIPTION",
            "PLUGIN_LICENSE",
            "LOAD_OPTION",
            "PLUGIN_MATURITY",
            "PLUGIN_AUTH_VERSION",
        ],
        "ENGINES": ["ENGINE", "SUPPORT", "COMMENT", "TRANSACTIONS", "XA", "SAVEPOINTS"],
        "KEY_COLUMN_USAGE": [
            "CONSTRAINT_CATALOG",
            "CONSTRAINT_SCHEMA",
            "CONSTRAINT_NAME",
            "TABLE_CATALOG",
            "TABLE_SCHEMA",
            "TABLE_NAME",
            "COLUMN_NAME",
            "ORDINAL_POSITION",
            "POSITION_IN_UNIQUE_CONSTRAINT",
            "REFERENCED_TABLE_SCHEMA",
            "REFERENCED_TABLE_NAME",
            "REFERENCED_COLUMN_NAME",
        ],
        "STATISTICS": [
            "TABLE_CATALOG",
            "TABLE_SCHEMA",
            "TABLE_NAME",
            "NON_UNIQUE",
            "INDEX_SCHEMA",
            "INDEX_NAME",
            "SEQ_IN_INDEX",
            "COLUMN_NAME",
            "COLLATION",
            "CARDINALITY",
            "SUB_PART",
            "PACKED",
            "NULLABLE",
            "INDEX_TYPE",
            "COMMENT",
            "INDEX_COMMENT",
            "IS_VISIBLE",
            "EXPRESSION",
        ],
        "CHARACTER_SETS": [
            "CHARACTER_SET_NAME",
            "DEFAULT_COLLATE_NAME",
            "DESCRIPTION",
            "MAXLEN",
        ],
        "COLLATIONS": [
            "COLLATION_NAME",
            "CHARACTER_SET_NAME",
            "ID",
            "IS_DEFAULT",
            "IS_COMPILED",
            "SORTLEN",
            "PAD_ATTRIBUTE",
        ],
        # MindsDB specific:
        "MODELS": [
            "NAME",
            "ENGINE",
            "PROJECT",
            "VERSION",
            "STATUS",
            "ACCURACY",
            "PREDICT",
            "UPDATE_STATUS",
            "MINDSDB_VERSION",
            "ERROR",
            "SELECT_DATA_QUERY",
            "TRAINING_OPTIONS",
            "CURRENT_TRAINING_PHASE",
            "TOTAL_TRAINING_PHASES",
            "TRAINING_PHASE_NAME",
            "TAG",
            "CREATED_AT",
            "TRAINING_TIME",
        ],
        "MODELS_VERSIONS": [
            "NAME",
            "ENGINE",
            "PROJECT",
            "ACTIVE",
            "VERSION",
            "STATUS",
            "ACCURACY",
            "PREDICT",
            "UPDATE_STATUS",
            "MINDSDB_VERSION",
            "ERROR",
            "SELECT_DATA_QUERY",
            "TRAINING_OPTIONS",
            "TAG",
            "CREATED_AT",
            "TRAINING_TIME",
        ],
        "DATABASES": ["NAME", "TYPE", "ENGINE", "CONNECTION_DATA"],
        "ML_ENGINES": ["NAME", "HANDLER", "CONNECTION_DATA"],
        "HANDLERS": [
            "NAME",
            "TYPE",
            "TITLE",
            "DESCRIPTION",
            "VERSION",
            "CONNECTION_ARGS",
            "IMPORT_SUCCESS",
            "IMPORT_ERROR",
        ],
        "JOBS": [
            "NAME",
            "PROJECT",
            "START_AT",
            "END_AT",
            "NEXT_RUN_AT",
            "SCHEDULE_STR",
            "QUERY",
            "VARIABLES",
        ],
        "MDB_TRIGGERS": ["NAME", "PROJECT", "DATABASE", "TABLE", "QUERY", "LAST_ERROR"],
        "JOBS_HISTORY": ["NAME", "PROJECT", "RUN_START", "RUN_END", "ERROR", "QUERY"],
        "CHATBOTS": [
            "NAME",
            "PROJECT",
            "DATABASE",
            "MODEL_NAME",
            "PARAMS",
            "IS_RUNNING",
            "LAST_ERROR",
        ],
        "KNOWLEDGE_BASES": ["NAME", "PROJECT", "MODEL", "STORAGE"],
        "SKILLS": ["NAME", "PROJECT", "TYPE", "PARAMS"],
        "AGENTS": [
            "NAME",
            "PROJECT",
            "MODEL_NAME",
            "SKILLS",
            "PARAMS"
        ]
    }

    def __init__(self, session):
        self.session = session
        self.integration_controller = session.integration_controller
        self.project_controller = ProjectController()
        self.database_controller = session.database_controller

        self.persis_datanodes = {}

        databases = self.database_controller.get_dict()
        if "files" in databases:
            self.persis_datanodes["files"] = IntegrationDataNode(
                "files",
                ds_type="file",
                integration_controller=self.session.integration_controller,
            )

        self.get_dataframe_funcs = {
            "TABLES": self._get_tables,
            "COLUMNS": self._get_columns,
            "SCHEMATA": self._get_schemata,
            "ENGINES": self._get_engines,
            "CHARACTER_SETS": self._get_charsets,
            "COLLATIONS": self._get_collations,
            "MODELS": self._get_models,
            "MODELS_VERSIONS": self._get_models_versions,
            "DATABASES": self._get_databases,
            "ML_ENGINES": self._get_ml_engines,
            "HANDLERS": self._get_handlers,
            "JOBS": self._get_jobs,
            "JOBS_HISTORY": self._get_jobs_history,
            "MDB_TRIGGERS": self._get_triggers,
            "CHATBOTS": self._get_chatbots,
            "KNOWLEDGE_BASES": self._get_knowledge_bases,
            "SKILLS": self._get_skills,
            "AGENTS": self._get_agents
        }
        for table_name in self.information_schema:
            if table_name not in self.get_dataframe_funcs:
                self.get_dataframe_funcs[table_name] = partial(
                    self._get_empty_table, table_name
                )

    def __getitem__(self, key):
        return self.get(key)

    def get(self, name):
        name_lower = name.lower()

        if name.lower() == "information_schema":
            return self

        if name_lower in self.persis_datanodes:
            return self.persis_datanodes[name_lower]

        existing_databases_meta = (
            self.database_controller.get_dict()
        )  # filter_type='project'
        database_name = None
        for key in existing_databases_meta:
            if key.lower() == name_lower:
                database_name = key
                break

        if database_name is None:
            return None

        database_meta = existing_databases_meta[database_name]
        if database_meta["type"] == "integration":
            integration = self.integration_controller.get(name=database_name)
            return IntegrationDataNode(
                database_name,
                ds_type=integration["engine"],
                integration_controller=self.session.integration_controller,
            )
        if database_meta["type"] == "project":
            project = self.database_controller.get_project(name=database_name)
            return ProjectDataNode(
                project=project,
                integration_controller=self.session.integration_controller,
                information_schema=self,
            )

        integration_names = self.integration_controller.get_all().keys()
        for integration_name in integration_names:
            if integration_name.lower() == name_lower:
                datasource = self.integration_controller.get(name=integration_name)
                return IntegrationDataNode(
                    integration_name,
                    ds_type=datasource["engine"],
                    integration_controller=self.session.integration_controller,
                )

        return None

    def has_table(self, tableName):
        tn = tableName.upper()
        if tn in self.information_schema:
            return True
        return False

    def get_table_columns(self, tableName):
        tn = tableName.upper()
        if tn in self.information_schema:
            return self.information_schema[tn]
        raise exc.ErTableExistError(
            f"Table information_schema.{tableName} does not exists"
        )

    def get_integrations_names(self):
        integration_names = self.integration_controller.get_all().keys()
        # remove files from list to prevent doubling in 'select from INFORMATION_SCHEMA.TABLES'
        return [x.lower() for x in integration_names if x not in ("files",)]

    def get_projects_names(self):
        projects = self.database_controller.get_dict(filter_type="project")
        return [x.lower() for x in projects]

    def _get_handlers(self, query: ASTNode = None):
        columns = self.information_schema["HANDLERS"]

        handlers = self.integration_controller.get_handlers_import_status()

        data = []
        for _key, val in handlers.items():
            connection_args = val.get("connection_args")
            if connection_args is not None:
                connection_args = str(dict(connection_args))
            import_success = val.get("import", {}).get("success")
            import_error = val.get("import", {}).get("error_message")
            data.append(
                [
                    val["name"],
                    val.get("type"),
                    val.get("title"),
                    val.get("description"),
                    val.get("version"),
                    connection_args,
                    import_success,
                    import_error,
                ]
            )

        df = pd.DataFrame(data, columns=columns)
        return df

    def _get_ml_engines(self, query: ASTNode = None):
        columns = self.information_schema["ML_ENGINES"]

        integrations = self.integration_controller.get_all()
        ml_integrations = {
            key: val for key, val in integrations.items() if val["type"] == "ml"
        }

        data = []
        for _key, val in ml_integrations.items():
            data.append([val["name"], val.get("engine"), val.get("connection_data")])

        df = pd.DataFrame(data, columns=columns)
        return df

    def _get_tables(self, query: ASTNode = None):
        columns = self.information_schema["TABLES"]

        target_table = None
        if (
            type(query) == Select
            and type(query.where) == BinaryOperation
            and query.where.op == "and"
        ):
            for arg in query.where.args:
                if (
                    type(arg) == BinaryOperation
                    and arg.op == "="
                    and type(arg.args[0]) == Identifier
                    and arg.args[0].parts[-1].upper() == "TABLE_SCHEMA"
                    and type(arg.args[1]) == Constant
                ):
                    target_table = arg.args[1].value
                    break

        data = []
        for name in self.information_schema.keys():
            if target_table is not None and target_table != name:
                continue
            row = TablesRow(TABLE_TYPE=TABLES_ROW_TYPE.SYSTEM_VIEW, TABLE_NAME=name)
            data.append(row.to_list())

        for ds_name, ds in self.persis_datanodes.items():
            if target_table is not None and target_table != ds_name:
                continue
            ds_tables = ds.get_tables()
            if len(ds_tables) == 0:
                continue
            elif isinstance(ds_tables[0], dict):
                ds_tables = [
                    TablesRow(
                        TABLE_TYPE=TABLES_ROW_TYPE.BASE_TABLE, TABLE_NAME=x["name"]
                    )
                    for x in ds_tables
                ]
            elif (
                isinstance(ds_tables, list)
                and len(ds_tables) > 0
                and isinstance(ds_tables[0], str)
            ):
                ds_tables = [
                    TablesRow(TABLE_TYPE=TABLES_ROW_TYPE.BASE_TABLE, TABLE_NAME=x)
                    for x in ds_tables
                ]
            for row in ds_tables:
                row.TABLE_SCHEMA = ds_name
                data.append(row.to_list())

        for ds_name in self.get_integrations_names():
            if target_table is not None and target_table != ds_name:
                continue
            try:
                ds = self.get(ds_name)
                ds_tables = ds.get_tables()
                for row in ds_tables:
                    row.TABLE_SCHEMA = ds_name
                    data.append(row.to_list())
            except Exception:
                print(f"Can't get tables from '{ds_name}'")

        for project_name in self.get_projects_names():
            if target_table is not None and target_table != project_name:
                continue
            project_dn = self.get(project_name)
            project_tables = project_dn.get_tables()
            for row in project_tables:
                row.TABLE_SCHEMA = project_name
                data.append(row.to_list())

        df = pd.DataFrame(data, columns=columns)
        return df

    def _get_jobs(self, query: ASTNode = None):
        jobs_controller = JobsController()

        project_name = None
        if (
            isinstance(query, Select)
            and type(query.where) == BinaryOperation
            and query.where.op == "="
            and query.where.args[0].parts == ["project"]
            and isinstance(query.where.args[1], Constant)
        ):
            project_name = query.where.args[1].value

        data = jobs_controller.get_list(project_name)

        columns = self.information_schema["JOBS"]
        columns_lower = [col.lower() for col in columns]

        # to list of lists
        data = [[row[k] for k in columns_lower] for row in data]

        return pd.DataFrame(data, columns=columns)

    def _get_jobs_history(self, query: ASTNode = None):
        jobs_controller = JobsController()

        project_name = None
        if (
            isinstance(query, Select)
            and type(query.where) == BinaryOperation
            and query.where.op == "="
            and query.where.args[0].parts == ["project"]
            and isinstance(query.where.args[1], Constant)
        ):
            project_name = query.where.args[1].value

        data = jobs_controller.get_history(project_name)

        columns = self.information_schema["JOBS_HISTORY"]
        columns_lower = [col.lower() for col in columns]

        # to list of lists
        data = [[row[k] for k in columns_lower] for row in data]

        return pd.DataFrame(data, columns=columns)

    def _get_triggers(self, query: ASTNode = None):
        from mindsdb.interfaces.triggers.triggers_controller import TriggersController

        triggers_controller = TriggersController()

        project_name = None
        if (
            isinstance(query, Select)
            and type(query.where) == BinaryOperation
            and query.where.op == "="
            and query.where.args[0].parts == ["project"]
            and isinstance(query.where.args[1], Constant)
        ):
            project_name = query.where.args[1].value

        data = triggers_controller.get_list(project_name)

        columns = self.information_schema["MDB_TRIGGERS"]
        columns_lower = [col.lower() for col in columns]

        # to list of lists
        data = [[row[k] for k in columns_lower] for row in data]

        return pd.DataFrame(data, columns=columns)

    def _get_chatbots(self, query: ASTNode = None):
        from mindsdb.interfaces.chatbot.chatbot_controller import ChatBotController

        chatbot_controller = ChatBotController()

        project_name = None
        if (
            isinstance(query, Select)
            and type(query.where) == BinaryOperation
            and query.where.op == "="
            and query.where.args[0].parts == ["project"]
            and isinstance(query.where.args[1], Constant)
        ):
            project_name = query.where.args[1].value

        data = chatbot_controller.get_chatbots(project_name)

        columns = self.information_schema["CHATBOTS"]
        columns_lower = [col.lower() for col in columns]

        # to list of lists
        data = [[row[k] for k in columns_lower] for row in data]

        return pd.DataFrame(data, columns=columns)

    def _get_knowledge_bases(self, query: ASTNode = None):
        from mindsdb.interfaces.knowledge_base.controller import KnowledgeBaseController
        controller = KnowledgeBaseController(self.session)
        project_name = None
        if (
                isinstance(query, Select)
                and type(query.where) == BinaryOperation
                and query.where.op == '='
                and query.where.args[0].parts == ['project']
                and isinstance(query.where.args[1], Constant)
        ):
            project_name = query.where.args[1].value

        # get the project id from the project name
        project_controller = ProjectController()
        project_id = project_controller.get(name=project_name).id
        kb_list = controller.list(project_id=project_id)

        columns = self.information_schema['KNOWLEDGE_BASES']

        # columns: NAME, PROJECT, MODEL, STORAGE
        data = [
            (
                kb.name,
                project_name,
                kb.embedding_model.name,
                kb.vector_database.name + '.' + kb.vector_database_table
            ) for kb in kb_list
        ]

        return pd.DataFrame(data, columns=columns)

    def _get_skills(self, query: ASTNode = None):
        skills_controller = SkillsController()
        project_name = None
        if (
                isinstance(query, Select)
                and type(query.where) == BinaryOperation
                and query.where.op == '='
                and query.where.args[0].parts == ['project']
                and isinstance(query.where.args[1], Constant)
        ):
            project_name = query.where.args[1].value

        all_skills = skills_controller.get_skills(project_name)

        columns = self.information_schema['SKILLS']

        # NAME, PROJECT, TYPE, PARAMS
        data = [(s.name, project_name, s.type, s.params) for s in all_skills]
        return pd.DataFrame(data, columns=columns)

    def _get_agents(self, query: ASTNode = None):
        agents_controller = AgentsController()
        project_name = None
        if (
                isinstance(query, Select)
                and type(query.where) == BinaryOperation
                and query.where.op == '='
                and query.where.args[0].parts == ['project']
                and isinstance(query.where.args[1], Constant)
        ):
            project_name = query.where.args[1].value

        all_agents = agents_controller.get_agents(project_name)

        columns = self.information_schema['AGENTS']

        # NAME, PROJECT, MODEL, SKILLS, PARAMS
        data = [(a.name, project_name, a.model_name, list(map(lambda s: s.name, a.skills)), a.params) for a in all_agents]
        return pd.DataFrame(data, columns=columns)

    def _get_databases(self, query: ASTNode = None):
        columns = self.information_schema["DATABASES"]

        project = self.database_controller.get_list()
        data = [
            [x["name"], x["type"], x["engine"], str(x.get("connection_data"))]
            for x in project
        ]

        df = pd.DataFrame(data, columns=columns)
        return df

    def _get_models(self, query: ASTNode = None):
        columns = self.information_schema["MODELS"]
        data = []
        for project_name in self.get_projects_names():
            project = self.database_controller.get_project(name=project_name)
            project_models = project.get_models()
            for row in project_models:
                table_name = row["name"]
                table_meta = row["metadata"]
                if table_meta["active"] is not True:
                    continue
                data.append(
                    [
                        table_name,
                        table_meta["engine"],
                        project_name,
                        table_meta["version"],
                        table_meta["status"],
                        table_meta["accuracy"],
                        table_meta["predict"],
                        table_meta["update_status"],
                        table_meta["mindsdb_version"],
                        table_meta["error"],
                        table_meta["select_data_query"],
                        table_meta["training_options"],
                        table_meta["current_training_phase"],
                        table_meta["total_training_phases"],
                        table_meta["training_phase_name"],
                        table_meta["label"],
                        row["created_at"],
                        table_meta["training_time"],
                    ]
                )
            # TODO optimise here
            # if target_table is not None and target_table != project_name:
            #     continue

        df = pd.DataFrame(data, columns=columns)
        return df

    def _get_models_versions(self, query: ASTNode = None):
        columns = self.information_schema["MODELS_VERSIONS"]
        data = []
        for project_name in self.get_projects_names():
            project = self.database_controller.get_project(name=project_name)
            project_models = project.get_models(active=None)
            for row in project_models:
                table_name = row["name"]
                table_meta = row["metadata"]
                data.append(
                    [
                        table_name,
                        table_meta["engine"],
                        project_name,
                        table_meta["active"],
                        table_meta["version"],
                        table_meta["status"],
                        table_meta["accuracy"],
                        table_meta["predict"],
                        table_meta["update_status"],
                        table_meta["mindsdb_version"],
                        table_meta["error"],
                        table_meta["select_data_query"],
                        table_meta["training_options"],
                        table_meta["label"],
                        row["created_at"],
                        table_meta["training_time"],
                    ]
                )

        df = pd.DataFrame(data, columns=columns)
        return df

    def _get_columns(self, query: ASTNode = None):
        columns = self.information_schema["COLUMNS"]

        # NOTE there is a lot of types in mysql, but listed below should be enough for our purposes
        row_templates = {
            "text": [
                "def",
                "SCHEMA_NAME",
                "TABLE_NAME",
                "COLUMN_NAME",
                "COL_INDEX",
                None,
                "YES",
                "varchar",
                1024,
                3072,
                None,
                None,
                None,
                "utf8",
                "utf8_bin",
                "varchar(1024)",
                None,
                None,
                "select",
                None,
                None,
            ],
            "timestamp": [
                "def",
                "SCHEMA_NAME",
                "TABLE_NAME",
                "COLUMN_NAME",
                "COL_INDEX",
                "CURRENT_TIMESTAMP",
                "YES",
                "timestamp",
                None,
                None,
                None,
                None,
                0,
                None,
                None,
                "timestamp",
                None,
                None,
                "select",
                None,
                None,
            ],
            "bigint": [
                "def",
                "SCHEMA_NAME",
                "TABLE_NAME",
                "COLUMN_NAME",
                "COL_INDEX",
                None,
                "YES",
                "bigint",
                None,
                None,
                20,
                0,
                None,
                None,
                None,
                "bigint unsigned",
                None,
                None,
                "select",
                None,
                None,
            ],
            "float": [
                "def",
                "SCHEMA_NAME",
                "TABLE_NAME",
                "COLUMN_NAME",
                "COL_INDEX",
                None,
                "YES",
                "float",
                None,
                None,
                12,
                0,
                None,
                None,
                None,
                "float",
                None,
                None,
                "select",
                None,
                None,
            ],
        }

        result = []

        for table_name in self.information_schema:
            table_columns = self.information_schema[table_name]
            for i, column_name in enumerate(table_columns):
                result_row = row_templates["text"].copy()
                result_row[1] = "information_schema"
                result_row[2] = table_name
                result_row[3] = column_name
                result_row[4] = i
                result.append(result_row)

        mindsdb_dn = self.get("MINDSDB")
        for table_row in mindsdb_dn.get_tables():
            table_name = table_row.TABLE_NAME
            table_columns = mindsdb_dn.get_table_columns(table_name)
            for i, column_name in enumerate(table_columns):
                result_row = row_templates["text"].copy()
                result_row[1] = "mindsdb"
                result_row[2] = table_name
                result_row[3] = column_name
                result_row[4] = i
                result.append(result_row)

        files_dn = self.get("FILES")
        for table_name in files_dn.get_tables():
            table_columns = files_dn.get_table_columns(table_name)
            for i, column_name in enumerate(table_columns):
                result_row = row_templates["text"].copy()
                result_row[1] = "files"
                result_row[2] = table_name
                result_row[3] = column_name
                result_row[4] = i
                result.append(result_row)

        df = pd.DataFrame(result, columns=columns)
        return df

    def _get_schemata(self, query: ASTNode = None):
        columns = self.information_schema["SCHEMATA"]

        databases_meta = self.session.database_controller.get_list()
        data = [
            ["def", x["name"], "utf8mb4", "utf8mb4_0900_ai_ci", None]
            for x in databases_meta
        ]

        df = pd.DataFrame(data, columns=columns)
        return df

    def _get_engines(self, query: ASTNode = None):
        columns = self.information_schema["ENGINES"]
        data = [
            [
                "InnoDB",
                "DEFAULT",
                "Supports transactions, row-level locking, and foreign keys",
                "YES",
                "YES",
                "YES",
            ]
        ]

        df = pd.DataFrame(data, columns=columns)
        return df

    def _get_charsets(self, query: ASTNode = None):
        columns = self.information_schema["CHARACTER_SETS"]
        data = [
            ["utf8", "UTF-8 Unicode", "utf8_general_ci", 3],
            ["latin1", "cp1252 West European", "latin1_swedish_ci", 1],
            ["utf8mb4", "UTF-8 Unicode", "utf8mb4_general_ci", 4],
        ]

        df = pd.DataFrame(data, columns=columns)
        return df

    def _get_collations(self, query: ASTNode = None):
        columns = self.information_schema["COLLATIONS"]
        data = [
            ["utf8_general_ci", "utf8", 33, "Yes", "Yes", 1, "PAD SPACE"],
            ["latin1_swedish_ci", "latin1", 8, "Yes", "Yes", 1, "PAD SPACE"],
        ]

        df = pd.DataFrame(data, columns=columns)
        return df

    def _get_empty_table(self, table_name, query: ASTNode = None):
        columns = self.information_schema[table_name]
        data = []

        df = pd.DataFrame(data, columns=columns)
        return df

    def query(self, query: ASTNode, session=None):
        query_tables = get_all_tables(query)

        if len(query_tables) != 1:
            raise exc.ErBadTableError(
                f"Only one table can be used in query to information_schema: {query}"
            )

        table_name = query_tables[0].upper()

        if table_name not in self.get_dataframe_funcs:
            raise exc.ErNotSupportedYet("Information schema: Not implemented.")

        dataframe = self.get_dataframe_funcs[table_name](query=query)
        data = query_df(dataframe, query, session=self.session)

        columns_info = [{"name": k, "type": v} for k, v in data.dtypes.items()]

        return data.to_dict(orient="records"), columns_info
