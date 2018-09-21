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
"""Contains Batfish client commands that query the Batfish service."""

from __future__ import absolute_import, print_function

import json
import logging
import os
import sys
import tempfile
from imp import new_module
from typing import Any, Dict, List, Optional, Union  # noqa: F401
from warnings import warn

from deprecated import deprecated
from requests import HTTPError

from pybatfish.client.consts import CoordConsts, WorkStatusCode
from pybatfish.datamodel import answer
from pybatfish.datamodel.answer.base import get_answer_text
from pybatfish.datamodel.answer.table import TableAnswer
from pybatfish.datamodel.primitives import Assertion, AssertionType
from pybatfish.datamodel.referencelibrary import NodeRoleDimension, \
    NodeRolesData, ReferenceBook, ReferenceLibrary
from pybatfish.exception import BatfishException
from pybatfish.settings.issues import IssueConfig  # noqa: F401
from pybatfish.util import (get_uuid, validate_name, zip_dir)
from . import resthelper, restv2helper, workhelper
from .options import Options
from .session import Session
from .workhelper import (_get_data_get_question_templates, get_work_status,
                         kill_work)

warn(
    "Pybatfish public API is being updated, note that API names and parameters will soon change.")

# TODO: normally libraries don't configure logging in code
_bfDebug = True
bf_logger = logging.getLogger("pybatfish.client")
bf_session = Session(bf_logger)

if _bfDebug:
    bf_logger.setLevel(logging.INFO)
    bf_logger.addHandler(logging.StreamHandler())
else:
    bf_logger.addHandler(logging.NullHandler())

__all__ = ['bf_add_analysis',
           'bf_add_issue_config',
           'bf_add_node_role_dimension',
           'bf_add_reference_book',
           'bf_auto_complete',
           'bf_configure_question',
           'bf_create_check',
           'bf_delete_analysis',
           'bf_delete_container',
           'bf_delete_issue_config',
           'bf_delete_network',
           'bf_delete_snapshot',
           'bf_delete_testrig',
           'bf_extract_answer_list',
           'bf_extract_answer_summary',
           'bf_generate_dataplane',
           'bf_get_analysis_answers',
           'bf_get_answer',
           'bf_get_info',
           'bf_get_issue_config',
           'bf_get_node_role_dimension',
           'bf_get_node_roles',
           'bf_get_reference_book',
           'bf_get_reference_library',
           'bf_get_work_status',
           'bf_init_analysis',
           'bf_init_container',
           'bf_init_snapshot',
           'bf_init_testrig',
           'bf_kill_work',
           'bf_list_analyses',
           'bf_list_containers',
           'bf_list_networks',
           'bf_list_incomplete_works',
           'bf_list_questions',
           'bf_list_snapshots',
           'bf_list_testrigs',
           'bf_logger',
           'bf_print_answer',
           'bf_read_question_settings',
           'bf_run_analysis',
           'bf_session',
           'bf_set_container',
           'bf_set_network',
           'bf_set_snapshot',
           'bf_set_testrig',
           'bf_str_answer',
           'bf_sync_snapshots_sync_now',
           'bf_sync_snapshots_update_settings',
           'bf_sync_testrigs_sync_now',
           'bf_sync_testrigs_update_settings',
           'bf_write_question_settings']


def bf_add_analysis(analysisName, questionDirectory):
    return _bf_init_or_add_analysis(analysisName, questionDirectory, False)


def bf_add_issue_config(issue_config):
    # type: (IssueConfig) -> None
    """
    Add or update the active network's configuration for an issue .

    :param issue_config: The IssueConfig object to add or update
    :type issue_config: :class:`pybatfish.settings.issues.IssueConfig`
    """
    restv2helper.add_issue_config(bf_session, issue_config)


def bf_add_node_role_dimension(dimension):
    # type: (NodeRoleDimension) -> None
    """
    Adds another role dimension to the active network.

    Individual roles within the dimension must have a valid (java) regex.
    The node list within those roles, if present, is ignored by the server.

    :param dimension: The NodeRoleDimension object for the dimension to add
    :type dimension: :class:`pybatfish.datamodel.referencelibrary.NodeRoleDimension`
    """
    if dimension.type == "AUTO":
        raise ValueError("Cannot add a dimension of type AUTO")
    restv2helper.add_node_role_dimension(bf_session, dimension)


def bf_add_reference_book(book):
    # type: (ReferenceBook) -> None
    """
    Adds another reference book to the active network.

    :param book: The ReferenceBook object to add
    :type book: :class:`pybatfish.datamodel.referencelibrary.ReferenceBook`
    """
    restv2helper.add_reference_book(bf_session, book)


def _bf_answer_obj(question_str, parameters_str, question_name,
                   background, snapshot, reference_snapshot):
    # type: (str, str, str, bool, str, Optional[str]) -> Union[str, Dict]

    json.loads(parameters_str)  # a syntactic check for parametersStr
    if not question_name:
        question_name = Options.default_question_prefix + "_" + get_uuid()

    # Upload the question
    json_data = workhelper.get_data_upload_question(bf_session, question_name,
                                                    question_str,
                                                    parameters_str)
    resthelper.get_json_response(bf_session,
                                 CoordConsts.SVC_RSC_UPLOAD_QUESTION, json_data)

    # Answer the question
    work_item = workhelper.get_workitem_answer(bf_session, question_name,
                                               snapshot, reference_snapshot)
    answer_dict = workhelper.execute(work_item, bf_session, background)
    if background:
        return work_item.id
    return answer.from_string(answer_dict["answer"])


def bf_auto_complete(completionType, query, maxSuggestions=None):
    """Auto complete the partial query based on its type."""
    jsonData = workhelper.get_data_auto_complete(bf_session, completionType,
                                                 query, maxSuggestions)
    response = resthelper.get_json_response(bf_session,
                                            CoordConsts.SVC_RSC_AUTO_COMPLETE,
                                            jsonData)
    if CoordConsts.SVC_KEY_SUGGESTIONS in response:
        return response[CoordConsts.SVC_KEY_SUGGESTIONS]
    else:
        bf_logger.error("Unexpected response: " + str(response))
        return None


def bf_configure_question(inQuestion, exceptions=None, assertion=None):
    """
    Get a new question template by adding the supplied exceptions and assertions.

    :param inQuestion: The question to use as a starting point
    :type inQuestion: :class:`pybatfish.question.question.QuestionBase`
    :param exceptions: Exceptions to add to the template.
        - `None` means keep the existing set.
        - `[]` means wipe out the existing set
    :param assertion: Assertion to add to the template.
        - `None` means keep the original one.
        - empty string means wipe out the existing set

    :return: The changed template. If both exceptions and assertion are `None`,
        you may still not get back the original
        template but get a "flattened" version where the parameter values have
        been inlined.
    """
    jsonData = workhelper.get_data_configure_question_template(bf_session,
                                                               inQuestion,
                                                               exceptions,
                                                               assertion)
    response = resthelper.get_json_response(bf_session,
                                            CoordConsts.SVC_RSC_CONFIGURE_QUESTION_TEMPLATE,
                                            jsonData)
    if CoordConsts.SVC_KEY_QUESTION in response:
        return response[CoordConsts.SVC_KEY_QUESTION]
    else:
        bf_logger.error("Unexpected response: " + str(response))
        return None


def bf_create_check(inQuestion, snapshot=None, reference_snapshot=None):
    """
    Turn a question into a check.

    1) Adds answers on the current base (and delta if differential) testrig as exceptions.
    2) Asserts that the new count of answers is zero.

    If the original question had exceptions or assertions, they will be overridden.

    :param inQuestion: The question to use as a starting point
    :type inQuestion: :class:`pybatfish.question.question.QuestionBase`

    :return: The modified template with exceptions and assertions added.
    """
    snapshot = bf_session.get_snapshot(snapshot)
    if reference_snapshot is None and inQuestion.get_differential():
        raise ValueError(
            "reference_snapshot argument is required to create a differential check")

    # override exceptions before asking the question so we get all the answers
    inQuestionWithoutExceptions = bf_configure_question(inQuestion,
                                                        exceptions=[])
    inAnswer = _bf_answer_obj(inQuestionWithoutExceptions, snapshot=snapshot,
                              reference_snapshot=reference_snapshot).dict()
    exceptions = bf_extract_answer_list(inAnswer)
    assertion = Assertion(AssertionType.COUNT_EQUALS, 0)
    outQuestion = bf_configure_question(inQuestionWithoutExceptions,
                                        exceptions=exceptions,
                                        assertion=assertion)
    return outQuestion


def bf_delete_analysis(analysisName):
    jsonData = workhelper.get_data_delete_analysis(bf_session, analysisName)
    jsonResponse = resthelper.get_json_response(bf_session,
                                                CoordConsts.SVC_RSC_DEL_ANALYSIS,
                                                jsonData)
    return jsonResponse


@deprecated("Deprecated in favor of bf_delete_network(name)")
def bf_delete_container(containerName):
    """
    Delete container by name.

    .. deprecated:: 0.36.0 In favor of :py:func:`bf_delete_network`
    """
    bf_delete_network(containerName)


def bf_delete_issue_config(major, minor):
    # type: (str, str) -> None
    """Deletes the issue config for the active network."""
    restv2helper.delete_issue_config(bf_session, major, minor)


def bf_delete_network(name):
    # type: (str) -> None
    """
    Delete network by name.

    :param name: name of the network to delete
    :type name: string
    """
    if name is None:
        raise ValueError('Network to be deleted must be supplied')
    jsonData = workhelper.get_data_delete_network(bf_session, name)
    resthelper.get_json_response(bf_session, CoordConsts.SVC_RSC_DEL_NETWORK,
                                 jsonData)


def bf_delete_snapshot(name):
    # type: (str) -> None
    """
    Delete named snapshot from current network.

    :param name: name of the snapshot to delete
    :type name: string
    """
    _check_network()
    if name is None:
        raise ValueError('Snapshot to be deleted must be supplied')
    json_data = workhelper.get_data_delete_snapshot(bf_session, name)
    resthelper.get_json_response(bf_session, CoordConsts.SVC_RSC_DEL_SNAPSHOT,
                                 json_data)


@deprecated("Deprecated in favor of bf_delete_snapshot(name)")
def bf_delete_testrig(testrigName):
    """
    Delete named testrig from current network.

    :param testrigName: name of the testrig to delete
    :type testrigName: string

    .. deprecated:: 0.36.0 In favor of :py:func:`bf_delete_snapshot`
    """
    bf_delete_snapshot(testrigName)


def bf_extract_answer_list(answerJson, includeKeys=None):
    if "question" not in answerJson:
        bf_logger.error("question not found in answerJson")
        return None
    if "status" not in answerJson or answerJson["status"] != "SUCCESS":
        bf_logger.error("question was not answered successfully")
        return None
    question = answerJson["question"]
    if "JsonPathQuestion" not in question["class"]:
        bf_logger.error("exception creation only works to jsonpath questions")
        return None
    if "answerElements" not in answerJson or "results" not in \
            answerJson["answerElements"][0]:
        bf_logger.error(
            "unexpected packaging of answer: answerElements does not exist of is not (non-empty) list")
        return None
    '''
    Jsonpath questions/answers are annoyingly flexible: they allow for multiple answerElements and multiple path queries
    following usage in templates, we pick the first answerElement and the response for the first query.
    When the answer has no results, the "result" field is missing
    '''
    result = answerJson["answerElements"][0]["results"]["0"].get("result", {})
    return [val for key, val in result.items() if
            includeKeys is None or key in includeKeys]


def bf_extract_answer_summary(answerJson):
    """Get the answer for a previously asked question."""
    if "status" not in answerJson or answerJson["status"] != "SUCCESS":
        bf_logger.error("question was not answered successfully")
        return None
    if "summary" not in answerJson:
        bf_logger.error("summary not found in the answer")
        return None
    return answerJson["summary"]


def _bf_generate_dataplane(snapshot):
    # type: (str) -> Dict[str, str]
    workItem = workhelper.get_workitem_generate_dataplane(bf_session, snapshot)
    answerDict = workhelper.execute(workItem, bf_session)
    return answerDict


def bf_generate_dataplane(snapshot=None):
    # type: (Optional[str]) -> str
    """Generates the data plane for the supplied snapshot. If no snapshot argument is given, uses the last snapshot initialized."""
    snapshot = bf_session.get_snapshot(snapshot)
    answerDict = _bf_generate_dataplane(snapshot)
    answer = answerDict["answer"]
    return answer


def bf_get_analysis_answers(analysisName, snapshot=None,
                            reference_snapshot=None):
    # type: (str, str, Optional[str]) -> Any
    """Get the answers for a previously asked analysis."""
    snapshot = bf_session.get_snapshot(snapshot)
    jsonData = workhelper.get_data_get_analysis_answers(bf_session,
                                                        analysisName, snapshot,
                                                        reference_snapshot)
    jsonResponse = resthelper.get_json_response(bf_session,
                                                CoordConsts.SVC_RSC_GET_ANALYSIS_ANSWERS,
                                                jsonData)
    answersDict = json.loads(jsonResponse['answers'])
    return answersDict


def bf_get_answer(questionName, snapshot, reference_snapshot=None):
    # type: (str, str, Optional[str]) -> Any
    """
    Get the answer for a previously asked question.

    :param questionName: the unique identifier of the previously asked question
    :param snapshot: the snapshot the question is run on
    :param reference_snapshot: if present, the snapshot against which the answer
        was computed differentially.
    """
    jsonData = workhelper.get_data_get_answer(bf_session, questionName,
                                              snapshot, reference_snapshot)
    response = resthelper.get_json_response(bf_session,
                                            CoordConsts.SVC_RSC_GET_ANSWER,
                                            jsonData)
    answerJson = json.loads(response["answer"])
    return answerJson


def bf_get_info():
    jsonResponse = resthelper.get_json_response(bf_session, '', useHttpGet=True)
    return jsonResponse


def bf_get_issue_config(major, minor):
    # type: (str, str) -> IssueConfig
    """Returns the issue config for the active network."""
    return IssueConfig.from_dict(
        restv2helper.get_issue_config(bf_session, major, minor))


def bf_get_node_role_dimension(dimension):
    # type: (str) -> NodeRoleDimension
    """Returns the set of node roles for the active network."""
    return NodeRoleDimension.from_dict(
        restv2helper.get_node_role_dimension(bf_session, dimension))


def bf_get_node_roles():
    # type: () -> NodeRolesData
    """Returns the set of node roles for the active network."""
    return NodeRolesData.from_dict(restv2helper.get_node_roles(bf_session))


def bf_get_reference_book(book_name):
    # type: (str) -> ReferenceBook
    """Returns the reference book with the specified for the active network."""
    return ReferenceBook.from_dict(
        restv2helper.get_reference_book(bf_session, book_name))


def bf_get_reference_library():
    # type: () -> ReferenceLibrary
    """Returns the reference library for the active network."""
    return ReferenceLibrary.from_dict(
        restv2helper.get_reference_library(bf_session))


def bf_get_work_status(wItemId):
    return get_work_status(wItemId, bf_session)


def _bf_init_or_add_analysis(analysisName, questionDirectory, newAnalysis):
    from pybatfish.question.question import load_dir_questions
    _check_network()
    module_name = 'pybatfish.util.anonymous_module'
    module = new_module(module_name)
    sys.modules[module_name] = module
    q_names = load_dir_questions(questionDirectory, moduleName=module_name)
    questions = [(qname, getattr(module, qname)) for qname in q_names]
    analysis = dict()
    for o in questions:
        question_name = o[0]
        question_class = o[1]
        question = question_class().dict()
        analysis[question_name] = question
    analysis_str = json.dumps(analysis, indent=2, sort_keys=True)
    with tempfile.NamedTemporaryFile() as tempFile:
        analysis_filename = tempFile.name
        with open(analysis_filename, 'w') as analysisFile:
            analysisFile.write(analysis_str)
            analysisFile.flush()
        json_data = workhelper.get_data_configure_analysis(
            bf_session, newAnalysis, analysisName, analysis_filename, None)
        json_response = resthelper.get_json_response(
            bf_session, CoordConsts.SVC_RSC_CONFIGURE_ANALYSIS, json_data)
    return json_response


def bf_init_analysis(analysisName, questionDirectory):
    return _bf_init_or_add_analysis(analysisName, questionDirectory, True)


@deprecated("Deprecated in favor of bf_set_network(name, prefix)")
def bf_init_container(containerName=None,
                      containerPrefix=Options.default_network_prefix):
    """
    Initialize a new container.

    .. deprecated:: 0.36.0 In favor of :py:func:`bf_set_network`
    """
    bf_set_network(containerName, containerPrefix)


def bf_init_snapshot(upload, name=None, overwrite=False, background=False):
    # type: (str, Optional[str], bool, bool) -> Union[str, Dict[str, str]]
    """Initialize a new snapshot.

    :param upload: snapshot to upload
    :type upload: zip file or directory
    :param name: name of the snapshot to initialize
    :type name: string
    :param overwrite: whether or not to overwrite an existing snapshot with the
       same name
    :type overwrite: bool
    :param background: whether or not to run the task in the background
    :type background: bool
    :return: name of initialized snapshot, or JSON dictionary of task status if background=True
    :rtype: Union[str, Dict]
    """
    if bf_session.network is None:
        bf_set_network()

    if name is None:
        name = Options.default_snapshot_prefix + get_uuid()
    validate_name(name)

    if name in bf_list_snapshots():
        if overwrite:
            bf_delete_snapshot(name)
        else:
            raise ValueError(
                'A snapshot named ''{}'' already exists in network ''{}'''.format(
                    name, bf_session.network))

    file_to_send = upload
    if os.path.isdir(upload):
        temp_zip_file = tempfile.NamedTemporaryFile()
        zip_dir(upload, temp_zip_file)
        file_to_send = temp_zip_file.name

    json_data = workhelper.get_data_upload_snapshot(bf_session, name,
                                                    file_to_send)
    resthelper.get_json_response(bf_session,
                                 CoordConsts.SVC_RSC_UPLOAD_SNAPSHOT,
                                 json_data)

    work_item = workhelper.get_workitem_parse(bf_session, name)
    answer_dict = workhelper.execute(work_item, bf_session,
                                     background=background)
    if background:
        bf_session.baseSnapshot = name
        return answer_dict

    status = WorkStatusCode(answer_dict["status"])
    if status != WorkStatusCode.TERMINATEDNORMALLY:
        raise BatfishException(
            'Initializing snapshot {ss} failed with status {status}: {msg}'.format(
                ss=name,
                status=status,
                msg=answer_dict['answer']))
    else:
        bf_session.baseSnapshot = name
        bf_logger.info("Default snapshot is now set to %s",
                       bf_session.baseSnapshot)
        return bf_session.baseSnapshot


@deprecated(
    "Deprecated in favor of bf_init_snapshot(upload, delta, name, background)")
def bf_init_testrig(dirOrZipfile, testrigName=None,
                    background=False):
    """
    Initialize a new testrig.

    .. deprecated:: 0.36.0 In favor of :py:func:`bf_init_snapshot`
    """
    return bf_init_snapshot(upload=dirOrZipfile, name=testrigName,
                            background=background)


def bf_kill_work(wItemId):
    return kill_work(bf_session, wItemId)


def bf_list_analyses():
    _check_network()
    jsonData = workhelper.get_data_list_analyses(bf_session)
    jsonResponse = resthelper.get_json_response(bf_session,
                                                CoordConsts.SVC_RSC_LIST_ANALYSES,
                                                jsonData)
    answer = jsonResponse['analysislist']
    return answer


@deprecated("Deprecated in favor of bf_list_networks()")
def bf_list_containers():
    """
    List containers the session's API key can access.

    .. deprecated:: 0.36.0 In favor of :py:func:`bf_list_networks`
    """
    return bf_list_networks()


def bf_list_networks():
    # type: () -> List[str]
    """
    List networks the session's API key can access.

    :return: a list of network names
    """
    json_data = workhelper.get_data_list_networks(bf_session)
    json_response = resthelper.get_json_response(
        bf_session, CoordConsts.SVC_RSC_LIST_NETWORKS, json_data)

    return list(map(str, json_response['networklist']))


def bf_list_incomplete_works():
    jsonData = workhelper.get_data_list_incomplete_work(bf_session)
    jsonResponse = resthelper.get_json_response(bf_session,
                                                CoordConsts.SVC_RSC_LIST_INCOMPLETE_WORK,
                                                jsonData)
    return jsonResponse


def bf_list_questions():
    _check_network()
    jsonData = workhelper.get_data_list_questions(bf_session)
    jsonResponse = resthelper.get_json_response(bf_session,
                                                CoordConsts.SVC_RSC_LIST_QUESTIONS,
                                                jsonData)
    answer = jsonResponse['questionlist']
    return answer


def bf_list_snapshots(verbose=False):
    # type: (bool) -> Union[List[str], Dict]
    """
    List snapshots for the current network.

    :param verbose: If true, return the full output of Batfish, including
        snapshot metadata.

    :return: a list of snapshot names or the full json response containing
        snapshots and metadata (if `verbose=True`)
    """
    json_data = workhelper.get_data_list_snapshots(bf_session,
                                                   bf_session.network)
    json_response = resthelper.get_json_response(bf_session,
                                                 CoordConsts.SVC_RSC_LIST_SNAPSHOTS,
                                                 json_data)
    if verbose:
        return json_response

    return [s['testrigname'] for s in json_response['snapshotlist']]


@deprecated("Deprecated in favor of bf_list_snapshots()")
def bf_list_testrigs(currentContainerOnly=True):
    """
    List testrigs.

    .. deprecated:: 0.36.0 In favor of :py:func:`bf_list_snapshots`
    """
    container_name = None

    if currentContainerOnly:
        _check_network()
        container_name = bf_session.network

    json_data = workhelper.get_data_list_testrigs(bf_session, container_name)
    json_response = resthelper.get_json_response(bf_session,
                                                 CoordConsts.SVC_RSC_LIST_TESTRIGS,
                                                 json_data)
    return json_response


def bf_str_answer(answer_json):
    """Convert the Json answer to a string."""
    try:
        if "answerElements" in answer_json and "metadata" in \
                answer_json["answerElements"][0]:
            table_answer = TableAnswer(answer_json)
            return table_answer.table_data.to_string()
        else:
            return get_answer_text(answer_json)
    except Exception as error:
        return "Error getting answer text: {}\n Original Json:\n {}".format(
            error, json.dumps(answer_json, indent=2))


def bf_print_answer(answer_json):
    # type: (Dict) -> None
    """Print the given answer JSON to console."""
    print(bf_str_answer(answer_json))


def _bf_get_question_templates():
    jsonData = _get_data_get_question_templates(bf_session)
    jsonResponse = resthelper.get_json_response(bf_session,
                                                CoordConsts.SVC_RSC_GET_QUESTION_TEMPLATES,
                                                jsonData)
    return jsonResponse[CoordConsts.SVC_KEY_QUESTION_LIST]


def bf_read_question_settings(question_class, json_path=None):
    # type: (str, Optional[List[str]]) -> Dict[str, Any]
    """
    Retrieves the network-wide JSON settings tree for the specified question class.

    :param question_class: The class of question whose settings are to be read
    :type question_class: string
    :param json_path: If supplied, return only the subtree reached by successively
        traversing each key in json_path starting from the root.
    :type json_path: list

    """
    return restv2helper.read_question_settings(bf_session, question_class,
                                               json_path)


def bf_run_analysis(analysisName, snapshot, reference_snapshot=None):
    # type: (str, str, Optional[str]) -> str
    workItem = workhelper.get_workitem_run_analysis(bf_session, analysisName,
                                                    snapshot,
                                                    reference_snapshot)
    workAnswer = workhelper.execute(workItem, bf_session)
    # status = workAnswer["status"]
    answer = workAnswer["answer"]
    return answer


@deprecated("Deprecated in favor of bf_set_network(name)")
def bf_set_container(containerName):
    """
    Set the current container by name.

    .. deprecated:: 0.36.0 In favor of :py:func:`bf_set_network`
    """
    bf_set_network(containerName)


def bf_set_network(name=None, prefix=Options.default_network_prefix):
    # type: (str, str) -> str
    """
    Configure the network used for analysis.

    :param name: name of the network to set. If `None`, a name will be generated using prefix.
    :type name: string
    :param prefix: prefix to prepend to auto-generated network names if name is empty
    :type name: string

    :return: The name of the configured network, if configured successfully.
    :rtype: string
    :raises BatfishException: if configuration fails
    """
    if name is None:
        name = prefix + get_uuid()
    validate_name(name, "network")

    try:
        net = restv2helper.get_network(bf_session, name)
        bf_session.network = str(net['name'])
        return bf_session.network
    except HTTPError as e:
        if e.response.status_code != 404:
            raise BatfishException('Unknown error accessing network', e)

    json_data = workhelper.get_data_init_network(bf_session, name)
    json_response = resthelper.get_json_response(
        bf_session, CoordConsts.SVC_RSC_INIT_NETWORK, json_data)

    network_name = json_response.get(CoordConsts.SVC_KEY_NETWORK_NAME)
    if network_name is None:
        raise BatfishException(
            "Network initialization failed. Server response: {}".format(
                json_response))

    bf_session.network = str(network_name)
    return bf_session.network


def bf_set_snapshot(name=None, index=None):
    # type: (Optional[str], Optional[int]) -> str
    """
    Set the current snapshot by name or index.

    :param name: name of the snapshot to set as the current snapshot
    :type name: string
    :param index: set the current snapshot to the ``index``-th most recent snapshot
    :type index: int
    :return: the name of the successfully set snapshot
    :rtype: str
    """
    if name is None and index is None:
        raise ValueError('One of name and index must be set')
    if name is not None and index is not None:
        raise ValueError('Only one of name and index can be set')

    snapshots = bf_list_snapshots()

    # Index specified, simply give the ith snapshot
    if index is not None:
        if not (-len(snapshots) <= index < len(snapshots)):
            raise IndexError(
                "Server has only {} snapshots: {}".format(
                    len(snapshots), snapshots))
        bf_session.baseSnapshot = snapshots[index]

    # Name specified, make sure it exists.
    else:
        assert name is not None  # type-hint to Python
        if name not in snapshots:
            raise ValueError(
                'No snapshot named ''{}'' was found in network ''{}'': {}'.format(
                    name, bf_session.network, snapshots))
        bf_session.baseSnapshot = name

    bf_logger.info("Default snapshot is now set to %s", bf_session.baseSnapshot)
    return bf_session.baseSnapshot


@deprecated("Deprecated in favor of bf_set_snapshot(name)")
def bf_set_testrig(testrigName):
    """
    Set the current testrig and environment by name.

    .. deprecated:: 0.36.0 In favor of :py:func:`bf_set_snapshot`
    """
    bf_set_snapshot(testrigName)


def bf_sync_snapshots_sync_now(plugin, force=False):
    """
    Synchronize snapshots with specified plugin.

    :param plugin: name of the plugin to sync snapshots with
    :type plugin: string
    :param force: whether or not to overwrite any conflicts
    :type force: bool
    :return: json response containing result of snapshot sync from Batfish service
    :rtype: dict
    """
    json_data = workhelper.get_data_sync_snapshots_sync_now(bf_session, plugin,
                                                            force)
    json_response = resthelper.get_json_response(bf_session,
                                                 CoordConsts.SVC_RSC_SYNC_SNAPSHOTS_SYNC_NOW,
                                                 json_data)
    return json_response


@deprecated(
    "Deprecated in favor of bf_sync_snapshots_sync_now(plugin_id, force)")
def bf_sync_testrigs_sync_now(pluginId, force=False):
    """
    Synchronize snapshots with specified plugin.

    .. deprecated:: 0.36.0 In favor of :py:func:`bf_sync_snapshots_sync_now`
    """
    return bf_sync_snapshots_sync_now(pluginId, force)


def bf_sync_snapshots_update_settings(plugin, settings):
    """
    Update snapshot sync settings for the specified plugin.

    :param plugin: name of the plugin to update
    :type plugin: string
    :param settings: settings to update
    :type settings: dict
    :return: json response containing result of settings update from Batfish service
    :rtype: dict
    """
    json_data = workhelper.get_data_sync_snapshots_update_settings(bf_session,
                                                                   plugin,
                                                                   settings)
    json_response = resthelper.get_json_response(bf_session,
                                                 CoordConsts.SVC_RSC_SYNC_SNAPSHOTS_UPDATE_SETTINGS,
                                                 json_data)
    return json_response


@deprecated(
    "Deprecated in favor of bf_sync_snapshots_update_settings(plugin_id, settings)")
def bf_sync_testrigs_update_settings(pluginId, settingsDict):
    """
    Synchronize snapshots with specified plugin.

    .. deprecated:: 0.36.0 In favor of :py:func:`bf_sync_snapshots_update_settings`
    """
    return bf_sync_snapshots_update_settings(pluginId, settingsDict)


def bf_write_question_settings(settings, question_class, json_path=None):
    # type: (Dict[str, Any], str, Optional[List[str]]) -> None
    """
    Write the network-wide JSON settings tree for the specified question class.

    :param settings: The JSON representation of the settings to be written
    :type settings: dict
    :param question_class: The class of question to configure
    :type question_class: string
    :param json_path: If supplied, write settings to the subtree reached by successively
        traversing each key in json_path starting from the root. Any absent keys along
        the path will be created.
    :type json_path: list

    """
    restv2helper.write_question_settings(bf_session, settings, question_class,
                                         json_path)


def _check_network():
    """Check if current network is set."""
    if bf_session.network is None:
        raise BatfishException("Network is not set")
