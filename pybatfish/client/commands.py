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
import tempfile
from typing import Any, Dict, List, Optional, Union  # noqa: F401

from deprecated import deprecated

from pybatfish.client.consts import CoordConsts, WorkStatusCode
from pybatfish.datamodel.primitives import (  # noqa: F401
    AutoCompleteSuggestion,
    Interface,
    VariableType,
)
from pybatfish.datamodel.referencelibrary import (
    NodeRoleDimension,
    NodeRolesData,
    ReferenceBook,
    ReferenceLibrary,
)
from pybatfish.exception import BatfishException
from pybatfish.settings.issues import IssueConfig  # noqa: F401
from pybatfish.util import BfJsonEncoder
from . import resthelper, restv2helper, workhelper
from .options import Options
from .session import Session
from .workhelper import kill_work


def _configure_default_logging():
    logger = logging.getLogger("pybatfish")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())


# TODO: normally libraries don't configure logging in code
_configure_default_logging()
bf_session = Session(load_questions=False)

__all__ = [
    "bf_add_issue_config",
    "bf_add_node_role_dimension",
    "bf_add_reference_book",
    "bf_auto_complete",
    "bf_delete_issue_config",
    "bf_delete_network",
    "bf_delete_node_role_dimension",
    "bf_delete_reference_book",
    "bf_delete_snapshot",
    "bf_extract_answer_summary",
    "bf_fork_snapshot",
    "bf_generate_dataplane",
    "bf_get_answer",
    "bf_get_issue_config",
    "bf_get_node_role_dimension",
    "bf_get_node_roles",
    "bf_get_reference_book",
    "bf_get_reference_library",
    "bf_get_snapshot_inferred_node_role_dimension",
    "bf_get_snapshot_inferred_node_roles",
    "bf_get_snapshot_node_role_dimension",
    "bf_get_snapshot_node_roles",
    "bf_get_work_status",
    "bf_init_snapshot",
    "bf_kill_work",
    "bf_list_networks",
    "bf_list_incomplete_works",
    "bf_list_snapshots",
    "bf_put_node_role_dimension",
    "bf_put_node_roles",
    "bf_read_question_settings",
    "bf_put_reference_book",
    "bf_session",
    "bf_set_network",
    "bf_set_snapshot",
    "bf_upload_diagnostics",
    "bf_write_question_settings",
]


def bf_add_issue_config(issue_config):
    # type: (IssueConfig) -> None
    """
    Add or update the active network's configuration for an issue .

    :param issue_config: The IssueConfig object to add or update
    :type issue_config: :class:`pybatfish.settings.issues.IssueConfig`
    """
    restv2helper.add_issue_config(bf_session, issue_config)


@deprecated(reason="Use bf_put_node_role_dimension")
def bf_add_node_role_dimension(dimension):
    bf_put_node_role_dimension(dimension)


@deprecated(reason="Use bf_put_reference_book")
def bf_add_reference_book(book):
    bf_put_reference_book(book)


def bf_auto_complete(completion_type, query, max_suggestions=None):
    # type: (VariableType, str, Optional[int]) -> List[AutoCompleteSuggestion]
    """
    Get a list of autocomplete suggestions that match the provided query based on the variable type.

    If completion is not supported for the provided variable type a BatfishException will be raised.

    Usage Example::

        >>> from pybatfish.client.commands import bf_auto_complete, bf_set_network
        >>> from pybatfish.datamodel.primitives import AutoCompleteSuggestion, VariableType
        >>> name = bf_set_network()
        >>> bf_auto_complete(VariableType.ROUTING_PROTOCOL_SPEC, "b") # doctest: +SKIP
        [AutoCompleteSuggestion(description=None, insertion_index=0, is_partial=False, rank=2147483647, text='bgp'),
            AutoCompleteSuggestion(description=None, insertion_index=0, is_partial=False, rank=2147483647, text='ebgp'),
            AutoCompleteSuggestion(description=None, insertion_index=0, is_partial=False, rank=2147483647, text='ibgp')]

    :param completion_type: The type of parameter to suggest autocompletions for
    :type completion_type: :class:`~pybatfish.datamodel.primitives.VariableType`
    :param query: The partial string to match suggestions on
    :type query: str
    :param max_suggestions: Optional max number of suggestions to be returned
    :type max_suggestions: int
    """
    jsonData = workhelper.get_data_auto_complete(
        bf_session, completion_type, query, max_suggestions
    )
    response = resthelper.get_json_response(
        bf_session, CoordConsts.SVC_RSC_AUTO_COMPLETE, jsonData
    )
    if CoordConsts.SVC_KEY_SUGGESTIONS in response:
        suggestions = [
            AutoCompleteSuggestion.from_dict(json.loads(suggestion))
            for suggestion in response[CoordConsts.SVC_KEY_SUGGESTIONS]
        ]
        return suggestions

    raise BatfishException("Unexpected response: {}.".format(response))


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
    bf_session.delete_network(name)


def bf_delete_node_role_dimension(dimension):
    # type: (str) -> None
    """Deletes the definition of the given role dimension for the active network."""
    bf_session.delete_node_role_dimension(dimension)


def bf_delete_reference_book(book_name):
    # type: (str) -> None
    """Deletes the reference book with the specified name for the active network."""
    bf_session.delete_reference_book(book_name)


def bf_delete_snapshot(name):
    # type: (str) -> None
    """
    Delete named snapshot from current network.

    :param name: name of the snapshot to delete
    :type name: string
    """
    bf_session.delete_snapshot(name)


def bf_extract_answer_summary(answer_dict):
    """Get the answer for a previously asked question."""
    if "status" not in answer_dict or answer_dict["status"] != "SUCCESS":
        raise BatfishException("Question was not answered successfully")
    if "summary" not in answer_dict:
        raise BatfishException("Summary not found in the answer")
    return answer_dict["summary"]


def bf_fork_snapshot(
    base_name,
    name=None,
    overwrite=False,
    background=False,
    deactivate_interfaces=None,
    deactivate_nodes=None,
    restore_interfaces=None,
    restore_nodes=None,
    add_files=None,
    extra_args=None,
):
    # type: (str, Optional[str], bool, bool, Optional[List[Interface]], Optional[List[str]], Optional[List[Interface]], Optional[List[str]], Optional[str], Optional[Dict[str, Any]]) -> Union[str, Dict, None]
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
    :param deactivate_nodes: list of names of nodes to deactivate in new snapshot
    :type deactivate_nodes: list[str]
    :param restore_interfaces: list of interfaces to reactivate
    :type restore_interfaces: list[Interface]
    :param restore_nodes: list of names of nodes to reactivate
    :type restore_nodes: list[str]
    :param add_files: path to zip file or directory containing files to add
    :type add_files: str
    :param extra_args: extra arguments to be passed to the parse command.
    :type extra_args: dict
    :return: name of initialized snapshot, JSON dictionary of task status if
        background=True, or None if the call fails
    :rtype: Union[str, Dict, None]
    """
    return bf_session._fork_snapshot(
        base_name,
        name=name,
        overwrite=overwrite,
        background=background,
        deactivate_interfaces=deactivate_interfaces,
        deactivate_nodes=deactivate_nodes,
        restore_interfaces=restore_interfaces,
        restore_nodes=restore_nodes,
        add_files=add_files,
        extra_args=extra_args,
    )


def bf_generate_dataplane(snapshot=None, extra_args=None):
    # type: (Optional[str], Optional[Dict[str, Any]]) -> str
    """Generates the data plane for the supplied snapshot. If no snapshot argument is given, uses the last snapshot initialized."""
    return bf_session.generate_dataplane(snapshot=snapshot, extra_args=extra_args)


def bf_get_answer(questionName, snapshot, reference_snapshot=None):
    # type: (str, str, Optional[str]) -> Any
    """
    Get the answer for a previously asked question.

    :param questionName: the unique identifier of the previously asked question
    :param snapshot: the snapshot the question is run on
    :param reference_snapshot: if present, the snapshot against which the answer
        was computed differentially.
    """
    return bf_session.get_answer(
        question=questionName, snapshot=snapshot, reference_snapshot=reference_snapshot
    )


def bf_get_issue_config(major, minor):
    # type: (str, str) -> IssueConfig
    """Returns the issue config for the active network."""
    return IssueConfig.from_dict(
        restv2helper.get_issue_config(bf_session, major, minor)
    )


def bf_get_node_role_dimension(dimension):
    # type: (str) -> NodeRoleDimension
    """Returns the definition of the given node role dimension for the active network."""
    return bf_session.get_node_role_dimension(dimension=dimension)


def bf_get_node_roles():
    # type: () -> NodeRolesData
    """Returns the definitions of node roles for the active network."""
    return bf_session.get_node_roles()


def bf_get_reference_book(book_name):
    # type: (str) -> ReferenceBook
    """Returns the reference book with the specified for the active network."""
    return bf_session.get_reference_book(name=book_name)


def bf_get_reference_library():
    # type: () -> ReferenceLibrary
    """Returns the reference library for the active network."""
    return bf_session.get_reference_library()


def bf_get_snapshot_inferred_node_roles():
    # type: () -> NodeRolesData
    """Gets suggested definitions and hypothetical assignments of node roles for the active network and snapshot."""
    return bf_session.get_node_roles(inferred=True)


def bf_get_snapshot_inferred_node_role_dimension(dimension):
    # type: (str) -> NodeRoleDimension
    """Gets the suggested definition and hypothetical assignments of node roles for the given inferred dimension for the active network and snapshot."""
    return bf_session.get_node_role_dimension(dimension, inferred=True)


def bf_get_snapshot_node_roles():
    # type: () -> NodeRolesData
    """Returns the definitions and assignments of node roles for the active network and snapshot."""
    return NodeRolesData.from_dict(restv2helper.get_snapshot_node_roles(bf_session))


def bf_get_snapshot_node_role_dimension(dimension):
    # type: (str) -> NodeRoleDimension
    """Returns the defintion and assignments of node roles for the given dimension for the active network and snapshot."""
    return NodeRoleDimension.from_dict(
        restv2helper.get_snapshot_node_role_dimension(bf_session, dimension)
    )


def bf_get_work_status(wItemId):
    return bf_session.get_work_status(work_item=wItemId)


def bf_init_snapshot(
    upload, name=None, overwrite=False, background=False, extra_args=None
):
    # type: (str, Optional[str], bool, bool, Optional[Dict[str, Any]]) -> Union[str, Dict[str, str]]
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
    :param extra_args: extra arguments to be passed to the parse command.
    :type extra_args: dict
    :return: name of initialized snapshot, or JSON dictionary of task status if background=True
    :rtype: Union[str, Dict]
    """
    return bf_session._init_snapshot(
        upload,
        name=name,
        overwrite=overwrite,
        background=background,
        extra_args=extra_args,
    )


def bf_kill_work(wItemId):
    return kill_work(bf_session, wItemId)


def bf_list_networks():
    # type: () -> List[str]
    """
    List networks the session's API key can access.

    :return: a list of network names
    """
    return bf_session.list_networks()


def bf_list_incomplete_works():
    return bf_session.list_incomplete_works()


def bf_list_snapshots(verbose=False):
    # type: (bool) -> Union[List[str], List[Dict[str,Any]]]
    """
    List snapshots for the current network.

    :param verbose: If true, return the full output of Batfish, including
        snapshot metadata.

    :return: a list of snapshot names or the full json response containing
        snapshots and metadata (if `verbose=True`)
    """
    return bf_session.list_snapshots(verbose=verbose)


def bf_put_reference_book(book):
    # type: (ReferenceBook) -> None
    """
    Put a reference book in the active network.

    If a book with the same name exists, it is overwritten.

    :param book: The ReferenceBook object to add
    :type book: :class:`pybatfish.datamodel.referencelibrary.ReferenceBook`
    """
    bf_session.put_reference_book(book)


def bf_put_node_role_dimension(dimension):
    # type: (NodeRoleDimension) -> None
    """
    Put a role dimension in the active network.

    Overwrites the old dimension if one of the same name already exists.

    Individual role dimension mappings within the dimension must have a valid (java) regex.

    :param dimension: The NodeRoleDimension object for the dimension to add
    :type dimension: :class:`pybatfish.datamodel.referencelibrary.NodeRoleDimension`
    """
    bf_session.put_node_role_dimension(dimension=dimension)


def bf_put_node_roles(node_roles_data):
    # type: (NodeRolesData) -> None
    """Writes the definitions of node roles for the active network. Completely replaces any existing definitions."""
    bf_session.put_node_roles(node_roles_data=node_roles_data)


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
    return restv2helper.read_question_settings(bf_session, question_class, json_path)


def bf_set_network(
    name: Optional[str] = None, prefix: str = Options.default_network_prefix
) -> str:
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
    return bf_session.set_network(name=name, prefix=prefix)


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
    return bf_session.set_snapshot(name=name, index=index)


def bf_upload_diagnostics(
    dry_run: bool = True,
    netconan_config: Optional[str] = None,
    contact_info: Optional[str] = None,
    proxy: Optional[str] = None,
) -> str:
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

    If `contact_info` is supplied (e.g. email address), Batfish developers may
    contact you if they have follow-up questions or to update you when the
    issues you encountered are resolved.

    :param dry_run: if True, upload is skipped and the anonymized files will be stored locally for review. If False, anonymized files will be uploaded to the Batfish developers
    :type dry_run: bool
    :param netconan_config: path to Netconan configuration file
    :type netconan_config: string
    :param contact_info: optional contact info associated with this upload
    :type contact_info: str
    :param proxy: a proxy URL to use when uploading data.
    :return: location of anonymized files (local directory if doing dry run, otherwise upload ID)
    :rtype: string
    """
    return bf_session.upload_diagnostics(
        dry_run=dry_run,
        netconan_config=netconan_config,
        contact_info=contact_info,
        proxy=proxy,
    )


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
    restv2helper.write_question_settings(
        bf_session, settings, question_class, json_path
    )


def _check_network():
    """Check if current network is set."""
    if bf_session.network is None:
        raise BatfishException("Network is not set")
