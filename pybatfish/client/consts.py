# coding=utf-8
#   Copyright 2018 The Batfish Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from enum import Enum


class BfConsts(object):
    """
    Contains constants derived from BfConsts.java in batfish-common.

    **IMPORTANT**:
    It is crucial to keep the two versions in sync.
    """

    ARG_ANALYSIS_NAME = "analysisname"
    ARG_ANSWER_JSON_PATH = "answerjsonpath"
    ARG_BLOCK_NAMES = "blocknames"
    ARG_CONTAINER_DIR = "containerdir"
    ARG_DELTA_TESTRIG = "deltatestrig"
    ARG_DIFF_ACTIVE = "diffactive"
    ARG_DIFFERENTIAL = "differential"
    ARG_HALT_ON_CONVERT_ERROR = "haltonconverterror"
    ARG_HALT_ON_PARSE_ERROR = "haltonparseerror"
    ARG_IGNORE_FILES_WITH_STRINGS = "ignorefileswithstrings"
    ARG_LOG_FILE = "logfile"
    ARG_LOG_LEVEL = "loglevel"
    ARG_PEDANTIC_AS_ERROR = "pedanticerror"
    ARG_PEDANTIC_SUPPRESS = "pedanticsuppress"
    ARG_PLUGIN_DIRS = "plugindirs"
    ARG_PRETTY_PRINT_ANSWER = "ppa"
    ARG_QUESTION_NAME = "questionname"
    ARG_RED_FLAG_AS_ERROR = "redflagerror"
    ARG_RED_FLAG_SUPPRESS = "redflagsuppress"
    ARG_SYNTHESIZE_JSON_TOPOLOGY = "synthesizejsontopology"
    ARG_SYNTHESIZE_TOPOLOGY = "synthesizetopology"
    ARG_TASK_PLUGIN = "taskplugin"
    ARG_TESTRIG = "testrig"
    ARG_UNIMPLEMENTED_AS_ERROR = "unimplementederror"
    ARG_UNIMPLEMENTED_SUPPRESS = "unimplementedsuppress"
    ARG_UNRECOGNIZED_AS_RED_FLAG = "urf"
    ARG_USE_PRECOMPUTED_ADVERTISEMENTS = "useprecomputedadvertisements"
    ARG_USE_PRECOMPUTED_IBGP_NEIGHBORS = "useprecomputedibgpneighbors"
    ARG_USE_PRECOMPUTED_ROUTES = "useprecomputedroutes"
    ARG_VERBOSE_PARSE = "verboseparse"

    COMMAND_ANALYZE = "analyze"
    COMMAND_ANSWER = "answer"
    COMMAND_DUMP_DP = "dp"
    COMMAND_INIT_INFO = "initinfo"
    COMMAND_PARSE_VENDOR_INDEPENDENT = "si"
    COMMAND_PARSE_VENDOR_SPECIFIC = "sv"
    COMMAND_QUERY = "query"
    COMMAND_REPORT = "report"
    COMMAND_VALIDATE_ENVIRONMENT = "venv"
    COMMAND_WRITE_ADVERTISEMENTS = "writeadvertisements"
    COMMAND_WRITE_IBGP_NEIGHBORS = "writeibgpneighbors"
    COMMAND_WRITE_ROUTES = "writeroutes"

    KEY_BGP_ANNOUNCEMENTS = "Announcements"

    PROP_METADATA = "metadata"
    PROP_NAME = "name"
    PROP_QUESTION_PLUGIN_DIR = "batfishQuestionPluginDir"

    RELPATH_ANSWER_HTML = "answer.html"
    RELPATH_ANSWER_JSON = "answer.json"
    RELPATH_AWS_VPC_CONFIGS_DIR = "aws_vpc_configs"
    RELPATH_AWS_VPC_CONFIGS_FILE = "aws_vpc_configs"
    RELPATH_BASE = "base"
    RELPATH_CONFIG_FILE_NAME_ALLINONE = "allinone.properties"
    RELPATH_CONFIG_FILE_NAME_BATFISH = "batfish.properties"
    RELPATH_CONFIG_FILE_NAME_CLIENT = "client.properties"
    RELPATH_CONFIG_FILE_NAME_COORDINATOR = "coordinator.properties"
    RELPATH_CONFIGURATIONS_DIR = "configs"
    RELPATH_CONVERT_ANSWER_PATH = "convert_answer"
    RELPATH_DATA_PLANE_DIR = "dp"
    RELPATH_DIFF = "diff"
    RELPATH_EDGE_BLACKLIST_FILE = "edge_blacklist"
    RELPATH_EXTERNAL_BGP_ANNOUNCEMENTS = "external_bgp_announcements.json"
    RELPATH_FAILURE_QUERY_PREFIX = "failure-query"
    RELPATH_FLOWS_DUMP_DIR = "flowdump"
    RELPATH_HOST_CONFIGS_DIR = "hosts"
    RELPATH_INTERFACE_BLACKLIST_FILE = "interface_blacklist"
    RELPATH_MULTIPATH_QUERY_PREFIX = "multipath-query"
    RELPATH_NODE_BLACKLIST_FILE = "node_blacklist"
    RELPATH_PARSE_ANSWER_PATH = "parse_answer"
    RELPATH_PRECOMPUTED_ROUTES = "precomputedroutes"
    RELPATH_QUERIES_DIR = "queries"
    RELPATH_QUESTION_FILE = "question"
    RELPATH_QUESTION_PARAM_FILE = "parameters"
    RELPATH_QUESTIONS_DIR = "questions"
    RELPATH_TOPOLOGY_FILE = "topology"
    RELPATH_VENDOR_INDEPENDENT_CONFIG_DIR = "indep"
    RELPATH_VENDOR_SPECIFIC_CONFIG_DIR = "vendor"
    RELPATH_Z3_DATA_PLANE_FILE = "dataplane.smt2"

    SUFFIX_ANSWER_JSON_FILE = ".json"  # type: str
    SUFFIX_LOG_FILE = ".log"  # type: str

    SVC_BASE_RSC = "/batfishservice"
    SVC_DEL_CONTAINER_RSC = "delcontainer"
    SVC_DEL_QUESTION_RSC = "delquestion"
    SVC_DEL_WORKER_KEY = "delworker"
    SVC_FAILURE_KEY = "failure"
    SVC_GET_STATUS_RSC = "getstatus"
    SVC_GET_TASKSTATUS_RSC = "gettaskstatus"
    SVC_PORT = 9999
    SVC_RUN_TASK_RSC = "run"
    SVC_SUCCESS_KEY = "success"
    SVC_TASK_KEY = "task"
    SVC_TASKID_KEY = "taskid"


class WorkStatusCode(str, Enum):
    ASSIGNED = "ASSIGNED"
    ASSIGNMENTERROR = "ASSIGNMENTERROR"
    BLOCKED = "BLOCKED"
    CHECKINGSTATUS = "CHECKINGSTATUS"
    REQUEUEFAILURE = "REQUEUEFAILURE"
    TERMINATEDABNORMALLY = "TERMINATEDABNORMALLY"
    TERMINATEDBYUSER = "TERMINATEDBYUSER"
    TERMINATEDNORMALLY = "TERMINATEDNORMALLY"
    TRYINGTOASSIGN = "TRYINGTOASSIGN"
    UNASSIGNED = "UNASSIGNED"

    @staticmethod
    def is_terminated(work_status_code):
        # type: (WorkStatusCode) -> bool
        return work_status_code in [
            WorkStatusCode.ASSIGNMENTERROR,
            WorkStatusCode.REQUEUEFAILURE,
            WorkStatusCode.TERMINATEDABNORMALLY,
            WorkStatusCode.TERMINATEDBYUSER,
            WorkStatusCode.TERMINATEDNORMALLY,
        ]


class CoordConsts(object):
    """
    Contains constants derived from CoordConsts.java in batfish-common.

    **IMPORTANT**:
    It is crucial to keep the two versions in sync.
    """

    DEFAULT_API_KEY = "00000000000000000000000000000000"
    # Constants for where and how services are hosted
    SVC_CFG_POOL_MGR = "/batfishpoolmgr"
    SVC_CFG_POOL_PORT = 9998
    SVC_CFG_POOL_SSL_DISABLE = True
    SVC_CFG_WORK_MGR = "/batfishworkmgr"
    SVC_CFG_WORK_PORT = 9997
    SVC_CFG_WORK_SSL_DISABLE = True

    # Constants for the v2 coordinator APIs
    SVC_CFG_WORK_MGR2 = "/v2"
    SVC_CFG_WORK_V2_PORT = 9996
    HTTP_HEADER_BATFISH_APIKEY = "X-Batfish-Apikey"
    HTTP_HEADER_BATFISH_VERSION = "X-Batfish-Version"

    SVC_FILENAME_HDR = "FileName"

    # Various constants used as keys on multi-part form data
    SVC_KEY_ADD_WORKER = "addworker"
    SVC_KEY_ANALYSIS_LIST = "analysislist"
    SVC_KEY_ANALYSIS_NAME = "analysisname"
    SVC_KEY_ANALYSIS_TYPE = "analysistype"
    SVC_KEY_ANSWER = "answer"
    SVC_KEY_ANSWERS = "answers"
    SVC_KEY_API_KEY = "apikey"
    SVC_KEY_ASSERTION = "assertion"
    SVC_KEY_AUTO_ANALYZE = "autoanalyze"
    SVC_KEY_COMPLETION_TYPE = "completiontype"
    SVC_KEY_CONFIGURATION_NAME = "configurationname"
    SVC_KEY_DEL_ANALYSIS_QUESTIONS = "delanalysisquestions"
    SVC_KEY_DEL_WORKER = "delworker"
    SVC_KEY_EXCEPTIONS = "exceptions"
    SVC_KEY_FAILURE = "failure"
    SVC_KEY_FILE = "file"
    SVC_KEY_FILE2 = "file2"
    SVC_KEY_FORCE = "force"
    SVC_KEY_MAX_SUGGESTIONS = "maxsuggestions"
    SVC_KEY_NETWORK_LIST = "networklist"
    SVC_KEY_NETWORK_NAME = "networkname"
    SVC_KEY_NETWORK_PREFIX = "networkprefix"
    SVC_KEY_NEW_ANALYSIS = "newanalysis"
    SVC_KEY_OBJECT_NAME = "objectname"
    SVC_KEY_PLUGIN_ID = "pluginid"
    SVC_KEY_QUERY = "query"
    SVC_KEY_QUESTION = "question"
    SVC_KEY_QUESTION_LIST = "questionlist"
    SVC_KEY_QUESTION_NAME = "questionname"
    SVC_KEY_REFERENCE_SNAPSHOT_NAME = "referencesnapshotname"
    SVC_KEY_RESULT = "result"
    SVC_KEY_SETTINGS = "settings"
    SVC_KEY_SNAPSHOT_INFO = "snapshotinfo"
    SVC_KEY_SNAPSHOT_LIST = "snapshotlist"
    SVC_KEY_SNAPSHOT_METADATA = "snapshotmetadata"
    SVC_KEY_SNAPSHOT_NAME = "snapshotname"
    SVC_KEY_SUCCESS = "success"
    SVC_KEY_SUGGESTED = "suggested"
    SVC_KEY_SUGGESTIONS = "suggestions"
    SVC_KEY_TASKSTATUS = "taskstatus"
    SVC_KEY_VERBOSE = "verbose"
    SVC_KEY_VERSION = "version"
    SVC_KEY_WORK_LIST = "worklist"
    SVC_KEY_WORK_TYPE = "worktype"
    SVC_KEY_WORKID = "workid"
    SVC_KEY_WORKITEM = "workitem"
    SVC_KEY_WORKSPACE_NAME = "workspace"
    SVC_KEY_WORKSTATUS = "workstatus"
    SVC_KEY_ZIPFILE = "zipfile"

    # Constants for endpoints of various service calls
    SVC_RSC_AUTO_COMPLETE = "autocomplete"
    SVC_RSC_CHECK_API_KEY = "checkapikey"
    SVC_RSC_CONFIGURE_ANALYSIS = "configureanalysis"
    SVC_RSC_CONFIGURE_QUESTION_TEMPLATE = "configurequestiontemplate"
    SVC_RSC_DEL_ANALYSIS = "delanalysis"
    SVC_RSC_DEL_CONTAINER = "delcontainer"
    SVC_RSC_DEL_NETWORK = "delnetwork"
    SVC_RSC_DEL_QUESTION = "delquestion"
    SVC_RSC_DEL_SNAPSHOT = "delsnapshot"
    SVC_RSC_GET_ANALYSIS_ANSWERS = "getanalysisanswers"
    SVC_RSC_GET_ANSWER = "getanswer"
    SVC_RSC_GET_CONFIGURATION = "getconfiguration"
    SVC_RSC_GET_CONTAINER = "getcontainer"
    SVC_RSC_GET_DATAPLANING_WORK = "getdataplaningwork"
    SVC_RSC_GET_NETWORK = "getnetwork"
    SVC_RSC_GET_OBJECT = "getobject"
    SVC_RSC_GET_PARSING_RESULTS = "getparsingresults"
    SVC_RSC_GET_PARSING_WORK = "getparsingwork"
    SVC_RSC_GET_QUESTION_TEMPLATES = "getquestiontemplates"
    SVC_RSC_GET_WORKLOG = "getworklog"
    SVC_RSC_GET_WORKSTATUS = "getworkstatus"
    SVC_RSC_GETSTATUS = "getstatus"
    SVC_RSC_INIT_CONTAINER = "initcontainer"
    SVC_RSC_INIT_NETWORK = "initnetwork"
    SVC_RSC_KILL_WORK = "killwork"
    SVC_RSC_LIST_ANALYSES = "listanalyses"
    SVC_RSC_LIST_INCOMPLETE_WORK = "listincompletework"
    SVC_RSC_LIST_NETWORKS = "listnetworks"
    SVC_RSC_LIST_QUESTIONS = "listquestions"
    SVC_RSC_LIST_SNAPSHOTS = "listsnapshots"
    SVC_RSC_POOL_GET_QUESTION_TEMPLATES = "getquestiontemplates"
    SVC_RSC_POOL_GETSTATUS = "getstatus"
    SVC_RSC_POOL_UPDATE = "updatepool"
    SVC_RSC_PUT_OBJECT = "putobject"
    SVC_RSC_QUEUE_WORK = "queuework"
    SVC_RSC_SYNC_SNAPSHOTS_SYNC_NOW = "syncsnapshotssyncnow"
    SVC_RSC_SYNC_SNAPSHOTS_UPDATE_SETTINGS = "syncsnapshotsupdatesettings"
    SVC_RSC_UPLOAD_QUESTION = "uploadquestion"
    SVC_RSC_UPLOAD_SNAPSHOT = "uploadsnapshot"


class CoordConstsV2(object):
    """
    Contains constants derived from CoordConstsV2.java in batfish-common.

    **IMPORTANT**:
    It is crucial to keep the two versions in sync.
    """

    # The HTTP Header containing the client's API Key.
    HTTP_HEADER_BATFISH_APIKEY = "X-Batfish-Apikey"
    # The HTTP Header containing the client's version.
    HTTP_HEADER_BATFISH_VERSION = "X-Batfish-Version"

    QP_KEY = "key"
    QP_VERBOSE = "verbose"

    RSC_ANSWER = "answer"
    RSC_FORK = "fork"
    RSC_INFERRED_NODE_ROLES = "inferred_node_roles"
    RSC_INPUT = "input"
    RSC_ISSUES = "issues"
    RSC_NETWORK = "network"
    RSC_NETWORKS = "networks"
    RSC_NODE_ROLES = "noderoles"
    RSC_OBJECTS = "objects"
    RSC_QUESTIONS = "questions"
    RSC_QUESTION_TEMPLATES = "question_templates"
    RSC_REFERENCE_LIBRARY = "referencelibrary"
    RSC_SETTINGS = "settings"
    RSC_SNAPSHOTS = "snapshots"
    RSC_WORK_LOG = "worklog"
