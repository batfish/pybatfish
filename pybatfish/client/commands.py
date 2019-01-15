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

import base64
import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional, Union  # noqa: F401

import six
from requests import HTTPError

from pybatfish.client.consts import CoordConsts, WorkStatusCode
from pybatfish.client.diagnostics import (_upload_diagnostics,
                                          _warn_on_snapshot_failure)
from pybatfish.datamodel.primitives import (  # noqa: F401
    AutoCompleteSuggestion,
    VariableType, Edge,
    Interface)
from pybatfish.datamodel.referencelibrary import (NodeRoleDimension,
                                                  NodeRolesData, ReferenceBook,
                                                  ReferenceLibrary)
from pybatfish.exception import BatfishException
from pybatfish.settings.issues import IssueConfig  # noqa: F401
from pybatfish.util import (BfJsonEncoder, get_uuid, validate_name, zip_dir)
from . import resthelper, restv2helper, workhelper
from .options import Options
from .session import Session
from .workhelper import (get_work_status,
                         kill_work)

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
           'bf_delete_analysis',
           'bf_delete_issue_config',
           'bf_delete_network',
           'bf_delete_node_role_dimension',
           'bf_delete_reference_book',
           'bf_delete_snapshot',
           'bf_extract_answer_summary',
           'bf_fork_snapshot',
           'bf_generate_dataplane',
           'bf_get_analysis_answers',
           'bf_get_answer',
           'bf_get_info',
           'bf_get_issue_config',
           'bf_get_node_role_dimension',
           'bf_get_node_roles',
           'bf_get_reference_book',
           'bf_get_reference_library',
           'bf_get_snapshot_inferred_node_role_dimension',
           'bf_get_snapshot_inferred_node_roles',
           'bf_get_snapshot_node_role_dimension',
           'bf_get_snapshot_node_roles',
           'bf_get_work_status',
           'bf_init_analysis',
           'bf_init_snapshot',
           'bf_kill_work',
           'bf_list_analyses',
           'bf_list_networks',
           'bf_list_incomplete_works',
           'bf_list_questions',
           'bf_list_snapshots',
           'bf_logger',
           'bf_put_node_roles',
           'bf_read_question_settings',
           'bf_run_analysis',
           'bf_session',
           'bf_set_network',
           'bf_set_snapshot',
           'bf_upload_diagnostics',
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


def bf_auto_complete(completion_type, query, max_suggestions=None):
    # type: (VariableType, str, Optional[int]) -> List[AutoCompleteSuggestion]
    """
    Auto complete the partial query based on its type.

    :param completion_type: The type of parameter to suggest autocompletions for
    :type completion_type: :class:`~pybatfish.datamodel.primitives.VariableType`
    :param query: The partial string to match suggestions on
    :type query: str
    :param max_suggestions: Optional max number of suggestions to be returned
    :type max_suggestions: int
    """
    jsonData = workhelper.get_data_auto_complete(bf_session, completion_type,
                                                 query, max_suggestions)
    response = resthelper.get_json_response(bf_session,
                                            CoordConsts.SVC_RSC_AUTO_COMPLETE,
                                            jsonData)
    if CoordConsts.SVC_KEY_SUGGESTIONS in response:
        suggestions = [AutoCompleteSuggestion.from_dict(json.loads(suggestion))
                       for suggestion in
                       response[CoordConsts.SVC_KEY_SUGGESTIONS]]
        return suggestions

    raise BatfishException("Unexpected response: {}.".format(response))


def bf_delete_analysis(analysisName):
    jsonData = workhelper.get_data_delete_analysis(bf_session, analysisName)
    jsonResponse = resthelper.get_json_response(bf_session,
                                                CoordConsts.SVC_RSC_DEL_ANALYSIS,
                                                jsonData)
    return jsonResponse


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


def bf_delete_node_role_dimension(dimension):
    # type: (str) -> None
    """Deletes the definition of the given role dimension for the active network."""
    restv2helper.delete_node_role_dimension(bf_session, dimension)


def bf_delete_reference_book(book_name):
    # type: (str) -> None
    """Deletes the reference book with the specified name for the active network."""
    restv2helper.delete_reference_book(bf_session, book_name)


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


def bf_extract_answer_summary(answer_dict):
    """Get the answer for a previously asked question."""
    if "status" not in answer_dict or answer_dict["status"] != "SUCCESS":
        raise BatfishException("Question was not answered successfully")
    if "summary" not in answer_dict:
        raise BatfishException("Summary not found in the answer")
    return answer_dict["summary"]


def bf_fork_snapshot(base_name, name=None, overwrite=False,
                     background=False, deactivate_interfaces=None,
                     deactivate_links=None, deactivate_nodes=None,
                     restore_interfaces=None, restore_links=None,
                     restore_nodes=None, add_files=None):
    # type: (str, Optional[str], bool, bool, Optional[List[Interface]], Optional[List[Edge]], Optional[List[str]], Optional[List[Interface]], Optional[List[Edge]], Optional[List[str]], Optional[str]) -> Union[str, Dict, None]
    """Copy an existing snapshot and deactivate or reactivate specified interfaces, nodes, and links on the copy.

    :param base_name: name of the snapshot to copy
    :type base_name: string
    :param name: name of the snapshot to initialize
    :type name: string
    :param overwrite: whether or not to overwrite an existing snapshot with the
        same name
    :type overwrite: bool
    :param background: whether or not to run the task in the background
    :type background: bool
    :param deactivate_interfaces: list of interfaces to deactivate in new snapshot
    :type deactivate_interfaces: list[Interface]
    :param deactivate_links: list of links to deactivate in new snapshot
    :type deactivate_links: list[Edge]
    :param deactivate_nodes: list of names of nodes to deactivate in new snapshot
    :type deactivate_nodes: list[str]
    :param restore_interfaces: list of interfaces to reactivate
    :type restore_interfaces: list[Interface]
    :param restore_links: list of links to reactivate
    :type restore_links: list[Edge]
    :param restore_nodes: list of names of nodes to reactivate
    :type restore_nodes: list[str]
    :param add_files: path to zip file or directory containing files to add
    :type add_files: str
    :return: name of initialized snapshot, JSON dictionary of task status if
        background=True, or None if the call fails
    :rtype: Union[str, Dict, None]
    """
    if bf_session.network is None:
        raise ValueError('Network must be set to fork a snapshot.')

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

    encoded_file = None
    if add_files is not None:
        file_to_send = add_files
        if os.path.isdir(add_files):
            temp_zip_file = tempfile.NamedTemporaryFile()
            zip_dir(add_files, temp_zip_file)
            file_to_send = temp_zip_file.name

        if os.path.isfile(file_to_send):
            with open(file_to_send, "rb") as f:
                encoded_file = base64.b64encode(f.read()).decode('ascii')

    json_data = {
        "snapshotBase": base_name,
        "snapshotNew": name,
        "deactivateInterfaces": deactivate_interfaces,
        "deactivateLinks": deactivate_links,
        "deactivateNodes": deactivate_nodes,
        "restoreInterfaces": restore_interfaces,
        "restoreLinks": restore_links,
        "restoreNodes": restore_nodes,
        "zipFile": encoded_file
    }
    restv2helper.fork_snapshot(bf_session,
                               json_data)

    return _parse_snapshot(name, background)


def bf_generate_dataplane(snapshot=None):
    # type: (Optional[str]) -> str
    """Generates the data plane for the supplied snapshot. If no snapshot argument is given, uses the last snapshot initialized."""
    snapshot = bf_session.get_snapshot(snapshot)

    work_item = workhelper.get_workitem_generate_dataplane(bf_session, snapshot)
    answer_dict = workhelper.execute(work_item, bf_session)
    return str(answer_dict["status"].value)


def bf_get_analysis_answers(name, snapshot=None,
                            reference_snapshot=None):
    # type: (str, str, Optional[str]) -> Any
    """Get the answers for a previously asked analysis."""
    snapshot = bf_session.get_snapshot(snapshot)
    json_data = workhelper.get_data_get_analysis_answers(
        bf_session, name, snapshot, reference_snapshot)
    json_response = resthelper.get_json_response(
        bf_session, CoordConsts.SVC_RSC_GET_ANALYSIS_ANSWERS, json_data)
    answers_dict = json.loads(json_response['answers'])
    return answers_dict


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
    """Returns the definition of the given node role dimension for the active network."""
    return NodeRoleDimension.from_dict(
        restv2helper.get_node_role_dimension(bf_session, dimension))


def bf_get_node_roles():
    # type: () -> NodeRolesData
    """Returns the definitions of node roles for the active network."""
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


def bf_get_snapshot_inferred_node_roles():
    # type: () -> NodeRolesData
    """Gets suggested definitions and hypothetical assignments of node roles for the active network and snapshot."""
    return NodeRolesData.from_dict(
        restv2helper.get_snapshot_inferred_node_roles(bf_session))


def bf_get_snapshot_inferred_node_role_dimension(dimension):
    # type: (str) -> NodeRoleDimension
    """Gets the suggested definition and hypothetical assignments of node roles for the given inferred dimension for the active network and snapshot."""
    return NodeRoleDimension.from_dict(
        restv2helper.get_snapshot_inferred_node_role_dimension(bf_session,
                                                               dimension))


def bf_get_snapshot_node_roles():
    # type: () -> NodeRolesData
    """Returns the definitions and assignments of node roles for the active network and snapshot."""
    return NodeRolesData.from_dict(
        restv2helper.get_snapshot_node_roles(bf_session))


def bf_get_snapshot_node_role_dimension(dimension):
    # type: (str) -> NodeRoleDimension
    """Returns the defintion and assignments of node roles for the given dimension for the active network and snapshot."""
    return NodeRoleDimension.from_dict(
        restv2helper.get_snapshot_node_role_dimension(bf_session, dimension))


def bf_get_work_status(wItemId):
    return get_work_status(wItemId, bf_session)


def _bf_init_or_add_analysis(analysisName, questionDirectory, newAnalysis):
    from pybatfish.question.question import _load_questions_from_dir
    _check_network()
    questions = _load_questions_from_dir(questionDirectory)
    analysis = {
        question_name: question_class(question_name=question_name)
        for question_name, question_class in six.iteritems(questions)
    }
    with tempfile.NamedTemporaryFile() as tempFile:
        with open(tempFile.name, 'w') as analysisFile:
            json.dump(analysis, analysisFile, indent=2, sort_keys=True,
                      cls=BfJsonEncoder)
        json_data = workhelper.get_data_configure_analysis(
            bf_session, newAnalysis, analysisName, tempFile.name, None)
        json_response = resthelper.get_json_response(
            bf_session, CoordConsts.SVC_RSC_CONFIGURE_ANALYSIS, json_data)
    return json_response


def bf_init_analysis(analysisName, questionDirectory):
    return _bf_init_or_add_analysis(analysisName, questionDirectory, True)


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

    return _parse_snapshot(name, background)


def _parse_snapshot(name, background):
    # type: (str, bool) -> Union[str, Dict[str, str]]
    """Parse specified snapshot.

    :param name: name of the snapshot to initialize
    :type name: str
    :param background: whether or not to run the task in the background
    :type background: bool
    :return: name of initialized snapshot, or JSON dictionary of task status if background=True
    :rtype: Union[str, Dict]
    """
    work_item = workhelper.get_workitem_parse(bf_session, name)
    answer_dict = workhelper.execute(work_item, bf_session,
                                     background=background)
    if background:
        bf_session.baseSnapshot = name
        return answer_dict

    status = WorkStatusCode(answer_dict["status"])

    if status != WorkStatusCode.TERMINATEDNORMALLY:
        init_log = restv2helper.get_work_log(bf_session, name, work_item.id)
        raise BatfishException(
            'Initializing snapshot {ss} failed with status {status}\n{log}'.format(
                ss=name, status=status, log=init_log))
    else:
        bf_session.baseSnapshot = name
        bf_logger.info("Default snapshot is now set to %s",
                       bf_session.baseSnapshot)
        if bf_session.enable_diagnostics:
            _warn_on_snapshot_failure()

        return bf_session.baseSnapshot


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
    # type: (bool) -> Union[List[str], List[Dict[str,Any]]]
    """
    List snapshots for the current network.

    :param verbose: If true, return the full output of Batfish, including
        snapshot metadata.

    :return: a list of snapshot names or the full json response containing
        snapshots and metadata (if `verbose=True`)
    """
    return restv2helper.list_snapshots(bf_session, verbose)


def bf_put_node_roles(node_roles_data):
    # type: (NodeRolesData) -> None
    """Writes the definitions of node roles for the active network. Completely replaces any existing definitions."""
    restv2helper.put_node_roles(bf_session, node_roles_data)


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


def bf_run_analysis(name, snapshot, reference_snapshot=None):
    # type: (str, str, Optional[str]) -> Any
    work_item = workhelper.get_workitem_run_analysis(
        bf_session, name, snapshot, reference_snapshot)
    work_answer = workhelper.execute(work_item, bf_session)
    if work_answer["status"] != WorkStatusCode.TERMINATEDNORMALLY:
        raise BatfishException("Failed to run analysis")

    return bf_get_analysis_answers(name, snapshot, reference_snapshot)


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
        bf_session.baseSnapshot = str(snapshots[index])

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


def bf_upload_diagnostics(dry_run=True, netconan_config=None):
    # type: (bool, str) -> str
    """
    Fetch, anonymize, and optionally upload snapshot diagnostics information.

    This runs a series of diagnostic questions on the current snapshot
    (including collecting parsing and conversion information).

    The information collected is anonymized with
    `Netconan <https://github.com/intentionet/netconan>`_ which either
    anonymizes passwords and IP addresses (default) or uses the settings in
    the provided `netconan_config`.

    The anonymous information is then either saved locally (if `dry_run` is
    True) or uploaded to Batfish developers (if `dry_run` is False).  The
    uploaded information will be accessible only to Batfish developers and will
    be used to help diagnose any issues you encounter.

    :param dry_run: whether or not to skip upload; if False, anonymized files will be stored locally, otherwise anonymized files will be uploaded to Batfish developers
    :type dry_run: bool
    :param netconan_config: path to Netconan configuration file
    :type netconan_config: string
    :return: location of anonymized files (local directory if doing dry run, otherwise upload ID)
    :rtype: string
    """
    return _upload_diagnostics(dry_run=dry_run, netconan_config=netconan_config)


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
