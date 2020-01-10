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

from __future__ import absolute_import, print_function

import base64
import logging
import os
import tempfile
import zipfile
from typing import Any, Callable, Dict, IO, List, Optional, Text, Union  # noqa: F401

import pkg_resources
from deprecated import deprecated
from requests import HTTPError

from pybatfish.client import resthelper, restv2helper, workhelper
from pybatfish.client._diagnostics import upload_diagnostics, warn_on_snapshot_failure
from pybatfish.client._facts import get_facts, load_facts, validate_facts, write_facts
from pybatfish.client.asserts import (
    assert_filter_denies,
    assert_filter_has_no_unreachable_lines,
    assert_filter_permits,
    assert_flows_fail,
    assert_flows_succeed,
    assert_no_duplicate_router_ids,
    assert_no_forwarding_loops,
    assert_no_incompatible_bgp_sessions,
    assert_no_incompatible_ospf_sessions,
    assert_no_undefined_references,
    assert_no_unestablished_bgp_sessions,
)
from pybatfish.client.consts import CoordConsts, WorkStatusCode
from pybatfish.client.restv2helper import get_component_versions
from pybatfish.client.workhelper import get_work_status
from pybatfish.datamodel import (
    HeaderConstraints,
    Interface,
    NodeRoleDimension,
    NodeRolesData,
    ReferenceBook,
    ReferenceLibrary,
)
from pybatfish.datamodel.answer import Answer, TableAnswer  # noqa: F401
from pybatfish.datamodel.answer.table import is_table_ans
from pybatfish.exception import BatfishException
from pybatfish.question.question import Questions
from pybatfish.util import get_uuid, validate_name, zip_dir
from .options import Options


class Asserts(object):
    """Class containing assertions for a given Session."""

    def __init__(self, session):
        self.session = session

    def assert_filter_denies(
        self,
        filters,
        headers,
        startLocation=None,
        soft=False,
        snapshot=None,
        df_format="table",
    ):
        # type: (str, HeaderConstraints, Optional[str], bool, Optional[str], str) -> bool
        """
        Check if a filter (e.g., ACL) denies a specified set of flows.

        :param filters: the specification for the filter (filterSpec) to check
        :param headers: :py:class:`~pybatfish.datamodel.flow.HeaderConstraints`
        :param startLocation: LocationSpec indicating where a flow starts
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param snapshot: the snapshot on which to check the assertion
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        :return: True if the assertion passes
        """
        return assert_filter_denies(
            filters, headers, startLocation, soft, snapshot, self.session, df_format
        )

    def assert_filter_has_no_unreachable_lines(
        self, filters, soft=False, snapshot=None, df_format="table"
    ):
        # type: (str, bool, Optional[str], str) -> bool
        """
        Check that a filter (e.g. an ACL) has no unreachable lines.

        A filter line is considered unreachable if it will never match a packet,
        e.g., because its match condition is empty or covered completely by those of
        prior lines."

        :param filters: the specification for the filter (filterSpec) to check
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param snapshot: the snapshot on which to check the assertion
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        :return: True if the assertion passes
        """
        return assert_filter_has_no_unreachable_lines(
            filters, soft, snapshot, self.session, df_format
        )

    def assert_filter_permits(
        self,
        filters,
        headers,
        startLocation=None,
        soft=False,
        snapshot=None,
        df_format="table",
    ):
        # type: (str, HeaderConstraints, Optional[str], bool, Optional[str], str) -> bool
        """
        Check if a filter (e.g., ACL) permits a specified set of flows.

        :param filters: the specification for the filter (filterSpec) to check
        :param headers: :py:class:`~pybatfish.datamodel.flow.HeaderConstraints`
        :param startLocation: LocationSpec indicating where a flow starts
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param snapshot: the snapshot on which to check the assertion
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        :return: True if the assertion passes
        """
        return assert_filter_permits(
            filters, headers, startLocation, soft, snapshot, self.session, df_format
        )

    def assert_flows_fail(
        self, startLocation, headers, soft=False, snapshot=None, df_format="table"
    ):
        # type: (str, HeaderConstraints, bool, Optional[str], str) -> bool
        """
        Check if the specified set of flows, denoted by starting locations and headers, fail.

        :param startLocation: LocationSpec indicating where the flow starts
        :param headers: :py:class:`~pybatfish.datamodel.flow.HeaderConstraints`
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param snapshot: the snapshot on which to check the assertion
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        :return: True if the assertion passes
        """
        return assert_flows_fail(
            startLocation, headers, soft, snapshot, self.session, df_format
        )

    def assert_flows_succeed(
        self, startLocation, headers, soft=False, snapshot=None, df_format="table"
    ):
        # type: (str, HeaderConstraints, bool, Optional[str], str) -> bool
        """
        Check if the specified set of flows, denoted by starting locations and headers, succeed.

        :param startLocation: LocationSpec indicating where the flow starts
        :param headers: :py:class:`~pybatfish.datamodel.flow.HeaderConstraints`
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param snapshot: the snapshot on which to check the assertion
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        :return: True if the assertion passes
        """
        return assert_flows_succeed(
            startLocation, headers, soft, snapshot, self.session, df_format
        )

    def assert_no_duplicate_router_ids(
        self, snapshot=None, nodes=None, protocols=None, soft=False, df_format="table"
    ):
        # type: (Optional[str], Optional[str], Optional[List[str]], bool, str) -> bool
        """Assert that there are no duplicate router IDs present in the snapshot.

        :param snapshot: the snapshot on which to check the assertion
        :param nodes: the nodes on which to run the assertion
        :param protocols: the protocol on which to use the assertion, e.g. bgp, ospf, etc.
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        """
        return assert_no_duplicate_router_ids(
            snapshot, nodes, protocols, soft, self.session, df_format
        )

    def assert_no_forwarding_loops(self, snapshot=None, soft=False, df_format="table"):
        # type: (Optional[str], bool, str) -> bool
        """Assert that there are no forwarding loops in the snapshot.

        :param snapshot: the snapshot on which to check the assertion
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        """
        return assert_no_forwarding_loops(snapshot, soft, self.session, df_format)

    def assert_no_incompatible_bgp_sessions(
        self,
        nodes=None,
        remote_nodes=None,
        status=None,
        snapshot=None,
        soft=False,
        df_format="table",
    ):
        # type: (Optional[str], Optional[str], Optional[str], Optional[str], bool, str) -> bool
        """Assert that there are no incompatible BGP sessions present in the snapshot.

        :param nodes: search sessions with specified nodes on one side of the sessions.
        :param remote_nodes: search sessions with specified remote_nodes on other side of the sessions.
        :param status: select sessions matching the specified `BGP session status specifier <https://github.com/batfish/batfish/blob/master/questions/Parameters.md#bgp-session-compat-status-specifier>`_, if none is specified then all statuses other than `UNIQUE_MATCH`, `DYNAMIC_MATCH`, and `UNKNOWN_REMOTE` are selected.
        :param snapshot: the snapshot on which to check the assertion
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        """
        return assert_no_incompatible_bgp_sessions(
            nodes, remote_nodes, status, snapshot, soft, self.session, df_format
        )

    def assert_no_incompatible_ospf_sessions(
        self,
        nodes=None,
        remote_nodes=None,
        snapshot=None,
        soft=False,
        df_format="table",
    ):
        # type: (Optional[str], Optional[str], Optional[str], bool, str) -> bool
        """Assert that there are no incompatible or unestablished OSPF sessions present in the snapshot.

        :param nodes: search sessions with specified nodes on one side of the sessions.
        :param remote_nodes: search sessions with specified remote_nodes on other side of the sessions.
        :param snapshot: the snapshot on which to check the assertion
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        """
        return assert_no_incompatible_ospf_sessions(
            nodes, remote_nodes, snapshot, soft, self.session, df_format
        )

    def assert_no_unestablished_bgp_sessions(
        self,
        nodes=None,
        remote_nodes=None,
        snapshot=None,
        soft=False,
        df_format="table",
    ):
        # type: (Optional[str], Optional[str], Optional[str], bool, str) -> bool
        """Assert that there are no BGP sessions that are compatible but not established.

        :param nodes: search sessions with specified nodes on one side of the sessions.
        :param remote_nodes: search sessions with specified remote_nodes on other side of the sessions.
        :param snapshot: the snapshot on which to check the assertion
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        """
        return assert_no_unestablished_bgp_sessions(
            nodes, remote_nodes, snapshot, soft, self.session, df_format
        )

    def assert_no_undefined_references(
        self, snapshot=None, soft=False, df_format="table"
    ):
        # type: (Optional[str], bool, str) -> bool
        """Assert that there are no undefined references present in the snapshot.

        :param snapshot: the snapshot on which to check the assertion
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        """
        return assert_no_undefined_references(snapshot, soft, self.session, df_format)


class Session(object):
    """Keeps session configuration needed to connect to a Batfish server.

    :ivar host: The host of the batfish service
    :ivar port_v1: The port batfish service is running on (9997 by default)
    :ivar port_v2: The additional port of batfish service (9996 by default)
    :ivar ssl: Whether to use SSL when connecting to Batfish (False by default)
    :ivar api_key: Your API key
    """

    def __init__(
        self,
        host: str = Options.coordinator_host,
        port_v1: int = Options.coordinator_work_port,
        port_v2: int = Options.coordinator_work_v2_port,
        ssl: bool = Options.use_ssl,
        verify_ssl_certs: bool = Options.verify_ssl_certs,
        api_key: str = CoordConsts.DEFAULT_API_KEY,
        load_questions: bool = True,
    ):
        # Coordinator args
        self.host = host  # type: str
        self.port_v1 = port_v1  # type: int
        self._base_uri_v1 = CoordConsts.SVC_CFG_WORK_MGR  # type: str
        self.port_v2 = port_v2  # type: int
        self._base_uri_v2 = CoordConsts.SVC_CFG_WORK_MGR2  # type: str
        self.ssl = ssl  # type: bool
        self.verify_ssl_certs = verify_ssl_certs  # type: bool

        # Session args
        self.api_key = api_key  # type: str
        self.network = None  # type: Optional[str]
        self.snapshot = None  # type: Optional[str]

        # Objects to hold and manage questions and asserts
        self.q = Questions(self)
        self.asserts = Asserts(self)

        # Additional worker args
        self.additional_args = {}  # type: Dict

        self.elapsed_delay = 5  # type: int
        self.stale_timeout = 5  # type: int
        self.enable_diagnostics = True  # type: bool

        # Auto-load question templates
        if load_questions:
            self.q.load()

    # Support old property names
    @property  # type: ignore
    @deprecated(reason="Use the new additional_args field instead")
    def additionalArgs(self):
        return self.additional_args

    @additionalArgs.setter  # type: ignore
    @deprecated(reason="Use the new additional_args field instead")
    def additionalArgs(self, val):
        self.additional_args = val

    @property  # type: ignore
    @deprecated(reason="Use the new api_key field instead")
    def apiKey(self):
        return self.api_key

    @apiKey.setter  # type: ignore
    @deprecated(reason="Use the new api_key field instead")
    def apiKey(self, val):
        self.api_key = val

    @property  # type: ignore
    @deprecated(reason="Use the new snapshot field instead")
    def baseSnapshot(self):
        return self.snapshot

    @baseSnapshot.setter  # type: ignore
    @deprecated(reason="Use the new snapshot field instead")
    def baseSnapshot(self, val):
        self.snapshot = val

    @property  # type: ignore
    @deprecated(reason="Use the new host field instead")
    def coordinatorHost(self):
        return self.host

    @coordinatorHost.setter  # type: ignore
    @deprecated(reason="Use the new host field instead")
    def coordinatorHost(self, val):
        self.host = val

    @property  # type: ignore
    @deprecated(reason="Use the new port_v1 field instead")
    def coordinatorPort(self):
        return self.port_v1

    @coordinatorPort.setter  # type: ignore
    @deprecated(reason="Use the new port_v1 field instead")
    def coordinatorPort(self, val):
        self.port_v1 = val

    @property  # type: ignore
    @deprecated(reason="Use the new port_v2 field instead")
    def coordinatorPort2(self):
        return self.port_v2

    @coordinatorPort2.setter  # type: ignore
    @deprecated(reason="Use the new port_v2 field instead")
    def coordinatorPort2(self, val):
        self.port_v2 = val

    @property  # type: ignore
    @deprecated(reason="Use the new ssl field instead")
    def useSsl(self):
        return self.ssl

    @useSsl.setter  # type: ignore
    @deprecated(reason="Use the new ssl field instead")
    def useSsl(self, val):
        self.ssl = val

    @property  # type: ignore
    @deprecated(reason="Use the new verify_ssl_certs field instead")
    def verifySslCerts(self):
        return self.verify_ssl_certs

    @verifySslCerts.setter  # type: ignore
    @deprecated(reason="Use the new verify_ssl_certs field instead")
    def verifySslCerts(self, val):
        self.verify_ssl_certs = val

    @classmethod
    def get_session_types(cls):
        # type: () -> Dict[str, Callable]
        """Get a dict of possible session types mapping their names to session classes."""
        return {
            entry_point.name: entry_point.load()
            for entry_point in pkg_resources.iter_entry_points("batfish_session")
        }

    @classmethod
    def get(cls, type_="bf", **params):
        # type: (str, **Any) -> Session
        """Instantiate and return a Session object of the specified type with the specified params."""
        sessions = cls.get_session_types()
        session_module = sessions.get(type_)
        if session_module is None:
            raise ValueError(
                "Invalid session type. Specified type '{}' does not match any registered session type: {}".format(
                    type_, set(sessions.keys())
                )
            )
        session = session_module(**params)  # type: Session
        return session

    def _get_bf_version(self):
        # type: () -> Optional[Text]
        """Get the Batfish backend version."""
        return get_component_versions(self).get("Batfish")

    def delete_network(self, name):
        # type: (str) -> None
        """
        Delete network by name.

        :param name: name of the network to delete
        :type name: str
        """
        if name is None:
            raise ValueError("Network to be deleted must be supplied")
        restv2helper.delete_network(self, name)

    def delete_node_role_dimension(self, dimension):
        # type: (str) -> None
        """
        Deletes the definition of the given role dimension for the active network.

        :param dimension: name of the dimension to delete
        :type dimension: str
        """
        restv2helper.delete_node_role_dimension(self, dimension)

    def delete_reference_book(self, name):
        # type: (str) -> None
        """
        Deletes the reference book with the specified name for the active network.

        :param name: name of the reference book to delete
        :type name: str
        """
        restv2helper.delete_reference_book(self, name)

    def delete_snapshot(self, name):
        # type: (str) -> None
        """
        Delete specified snapshot from current network.

        :param name: name of the snapshot to delete
        :type name: str
        """
        self._check_network()
        assert self.network is not None  # guaranteed by _check_network
        if name is None:
            raise ValueError("Snapshot to be deleted must be supplied")
        restv2helper.delete_snapshot(self, name, self.network)

    def extract_facts(self, nodes="/.*/", output_directory=None, snapshot=None):
        # type: (Text, Optional[Text], Optional[Text]) -> Dict[Text, Any]
        """
        Extract and return a dictionary of facts about the specified nodes on a network snapshot.

        If a snapshot is specified, facts are collected for that snapshot, otherwise facts are collected for the current snapshot.

        If an output directory is specified, facts for each node will be written to a separate YAML file in that directory.

        :param nodes: `NodeSpecifier <https://github.com/batfish/batfish/blob/master/questions/Parameters.md#node-specifier>`_, specifying which nodes to extract facts for.
        :type nodes: Text
        :param output_directory: path to directory to write facts to
        :type output_directory: Text
        :param snapshot: name of the snapshot to extract facts for, defaults to the current snapshot
        :type snapshot: Text
        :return: facts about the specified nodes on the current network snapshot
        :rtype: dict
        """
        facts = get_facts(self, nodes, snapshot=snapshot)
        if output_directory:
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            if os.path.isfile(output_directory):
                raise ValueError(
                    "Cannot write facts to file, must be a directory: {}".format(
                        output_directory
                    )
                )
            write_facts(output_directory, facts)
        return facts

    def fork_snapshot(
        self,
        base_name,
        name=None,
        overwrite=False,
        deactivate_interfaces=None,
        deactivate_nodes=None,
        restore_interfaces=None,
        restore_nodes=None,
        add_files=None,
        extra_args=None,
    ):
        # type: (str, Optional[str], bool, Optional[List[Interface]], Optional[List[str]], Optional[List[Interface]], Optional[List[str]], Optional[str], Optional[Dict[str, Any]]) -> Optional[str]
        """
        Copy an existing snapshot and deactivate or reactivate specified interfaces, nodes, and links on the copy.

        :param base_name: name of the snapshot to copy
        :type base_name: str
        :param name: name of the snapshot to initialize
        :type name: str
        :param overwrite: whether or not to overwrite an existing snapshot with the
            same name
        :type overwrite: bool
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

        :return: name of initialized snapshot or None if the call fails
        :rtype: Optional[str]
        """
        ss_name = self._fork_snapshot(
            base_name,
            name=name,
            overwrite=overwrite,
            deactivate_interfaces=deactivate_interfaces,
            deactivate_nodes=deactivate_nodes,
            restore_interfaces=restore_interfaces,
            restore_nodes=restore_nodes,
            add_files=add_files,
            extra_args=extra_args,
        )
        assert isinstance(ss_name, str)  # Guaranteed since background=False
        return ss_name

    def _fork_snapshot(
        self,
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
        self._check_network()

        if name is None:
            name = Options.default_snapshot_prefix + get_uuid()
        validate_name(name)

        if name in self.list_snapshots():
            if overwrite:
                self.delete_snapshot(name)
            else:
                raise ValueError(
                    "A snapshot named "
                    "{}"
                    " already exists in network "
                    "{}"
                    ". "
                    "Use overwrite = True if you want to overwrite the "
                    "existing snapshot".format(name, self.network)
                )

        encoded_file = None
        if add_files is not None:
            file_to_send = add_files
            if os.path.isdir(add_files):
                temp_zip_file = tempfile.NamedTemporaryFile()
                zip_dir(add_files, temp_zip_file)
                file_to_send = temp_zip_file.name

            if os.path.isfile(file_to_send):
                with open(file_to_send, "rb") as f:
                    encoded_file = base64.b64encode(f.read()).decode("ascii")

        json_data = {
            "snapshotBase": base_name,
            "snapshotNew": name,
            "deactivateInterfaces": deactivate_interfaces,
            "deactivateNodes": deactivate_nodes,
            "restoreInterfaces": restore_interfaces,
            "restoreNodes": restore_nodes,
            "zipFile": encoded_file,
        }
        restv2helper.fork_snapshot(self, json_data)

        return self._parse_snapshot(name, background, extra_args)

    def generate_dataplane(self, snapshot=None, extra_args=None):
        # type: (Optional[str], Optional[Dict[str, Any]]) -> str
        """
        Generates the data plane for the supplied snapshot. If no snapshot is specified, uses the last snapshot initialized.

        :param snapshot: name of the snapshot to generate dataplane for
        :type snapshot: str
        :param extra_args: extra arguments to be passed to Batfish
        :type extra_args: dict
        """
        snapshot = self.get_snapshot(snapshot)

        work_item = workhelper.get_workitem_generate_dataplane(self, snapshot)
        answer_dict = workhelper.execute(work_item, self, extra_args=extra_args)
        return str(answer_dict["status"].value)

    def get_answer(self, question, snapshot, reference_snapshot=None):
        # type: (str, str, Optional[str]) -> Answer
        """
        Get the answer for a previously asked question.

        :param question: the unique identifier of the previously asked question
        :type question: str
        :param snapshot: name of the snapshot the question was run on
        :type snapshot: str
        :param reference_snapshot: if present, gets the answer for a differential question asked against the specified reference snapshot
        :type reference_snapshot: str
        :return: answer to the specified question
        :rtype: :py:class:`Answer`
        """
        params = {"snapshot": snapshot, "referenceSnapshot": reference_snapshot}
        ans = restv2helper.get_answer(self, question, params)
        if is_table_ans(ans):
            return TableAnswer(ans)
        else:
            return Answer(ans)

    def get_base_url(self):
        # type: () -> str
        """Generate the base URL for connecting to Batfish coordinator."""
        protocol = "https" if self.ssl else "http"
        return "{0}://{1}:{2}{3}".format(
            protocol, self.host, self.port_v1, self._base_uri_v1
        )

    def get_base_url2(self):
        # type: () -> str
        """Generate the base URL for V2 of the coordinator APIs."""
        protocol = "https" if self.ssl else "http"
        return "{0}://{1}:{2}{3}".format(
            protocol, self.host, self.port_v2, self._base_uri_v2
        )

    def get_node_role_dimension(self, dimension, inferred=False):
        # type: (str, bool) -> NodeRoleDimension
        """
        Returns the definition of the given node role dimension for the active network or inferred definition for the active snapshot.

        :param dimension: name of the node role dimension to fetch
        :type dimension: str
        :param inferred: whether or not to fetch active snapshot's inferred node role dimension
        :type inferred: bool

        :return: the definition of the given node role dimension for the active network, or inferred definition for the active snapshot if inferred=True.
        :rtype: :class:`~pybatfish.datamodel.referencelibrary.NodeRoleDimension`
        """
        if inferred:
            self._check_snapshot()
            return NodeRoleDimension.from_dict(
                restv2helper.get_snapshot_inferred_node_role_dimension(self, dimension)
            )
        return NodeRoleDimension.from_dict(
            restv2helper.get_node_role_dimension(self, dimension)
        )

    def get_node_roles(self, inferred=False):
        # type: (bool) -> NodeRolesData
        """
        Returns the definitions of node roles for the active network or inferred roles for the active snapshot.

        :param inferred: whether or not to fetch the active snapshot's inferred node roles
        :type inferred: bool

        :return: the definitions of node roles for the active network, or inferred definitions for the active snapshot if inferred=True.
        :rtype: :class:`~pybatfish.datamodel.referencelibrary.NodeRolesData`
        """
        if inferred:
            self._check_snapshot()
            return NodeRolesData.from_dict(
                restv2helper.get_snapshot_inferred_node_roles(self)
            )
        return NodeRolesData.from_dict(restv2helper.get_node_roles(self))

    def get_reference_book(self, name):
        # type: (str) -> ReferenceBook
        """
        Returns the specified reference book for the active network.

        :param name: name of the reference book to fetch
        :type name: str
        """
        return ReferenceBook.from_dict(restv2helper.get_reference_book(self, name))

    def get_reference_library(self):
        # type: () -> ReferenceLibrary
        """Returns the reference library for the active network."""
        return ReferenceLibrary.from_dict(restv2helper.get_reference_library(self))

    def get_snapshot(self, snapshot=None):
        # type: (Optional[Union[str, Text]]) -> str
        """
        Get the specified or active snapshot name.

        :param snapshot: if specified, this name is returned instead of active snapshot
        :type snapshot: str or Text

        :return: name of the active snapshot, or the specified snapshot if applicable
        :rtype: str

        :raises ValueError: if there is no active snapshot and no snapshot was specified
        """
        if snapshot is not None:
            return str(snapshot)
        elif self.snapshot is not None:
            return self.snapshot
        else:
            raise ValueError(
                "snapshot must be either provided or set using "
                "set_snapshot (e.g. bf_session.set_snapshot('NAME')"
            )

    def get_url(self, resource):
        # type: (str) -> str
        """
        Get URL for the specified resource.

        :param resource: URI of the requested resource
        :type resource: str
        """
        return "{0}/{1}".format(self.get_base_url(), resource)

    def get_work_status(self, work_item):
        """Get the status for the specified work item."""
        return get_work_status(work_item, self)

    def get_component_versions(self):
        # type: () -> Dict[str, Any]
        """Get a dictionary of backend components (e.g. Batfish, Z3) and their versions."""
        return get_component_versions(self)

    def init_snapshot(self, upload, name=None, overwrite=False, extra_args=None):
        # type: (str, Optional[str], bool, Optional[Dict[str, Any]]) -> str
        """
        Initialize a new snapshot.

        :param upload: path to the snapshot zip or directory
        :type upload: str
        :param name: name of the snapshot to initialize
        :type name: str
        :param overwrite: whether or not to overwrite an existing snapshot with the
           same name
        :type overwrite: bool
        :param extra_args: extra arguments to be passed to the parse command
        :type extra_args: dict

        :return: name of initialized snapshot
        :rtype: str
        """
        ss_name = self._init_snapshot(
            upload, name=name, overwrite=overwrite, extra_args=extra_args
        )
        assert isinstance(ss_name, str)  # Guaranteed since background=False
        return ss_name

    def init_snapshot_from_text(
        self,
        text,
        filename=None,
        snapshot_name=None,
        platform=None,
        overwrite=False,
        extra_args=None,
    ):
        # type: (str, Optional[str], Optional[str], Optional[str], bool, Optional[Dict[str, Any]]) -> str
        """
        Initialize a snapshot of a single configuration file with given text.

        When `platform=None` the file contains the given text, unmodified. This
        means that the file text must indicate the platform of the vendor to
        Batfish, which is usually learned from headers that devices add in
        "show run"::

            boot nxos bootflash:nxos.7.0.3.I4.7.bin   (Cisco NX-OS)
            ! boot system flash:/vEOS-lab.swi         (Arista EOS)
            #TMSH-VERSION: 1.0                        (F5 Big-IP)
            !! IOS XR Configuration 5.2.4             (Cisco IOS XR)

        Alternately, you may supply the name of the platform in the `platform`
        argument.

        As usual, the hostname of the node will be parsed from the configuration
        text itself, and if not present Batfish will default to the provided
        filename.

        :param text: the contents of the file.
        :type text: str
        :param filename: name of the configuration file created, 'config' by
            default.
        :type filename: str
        :param snapshot_name: name of the snapshot to initialize
        :type snapshot_name: str
        :param platform: the RANCID router.db name for the device platform,
            i.e., "cisco-nx", "arista", "f5", or "cisco-xr" for above examples.
            See https://www.shrubbery.net/rancid/man/router.db.5.html
        :type platform: str
        :param overwrite: whether or not to overwrite an existing snapshot with
           the same name.
        :type overwrite: bool
        :param extra_args: extra arguments to be passed to the parse command
        :type extra_args: dict

        :return: name of initialized snapshot
        :rtype: str
        """
        if filename is None:
            filename = "config"

        data = _create_in_memory_zip(text, filename, platform)
        ss_name = self._init_snapshot(
            data, name=snapshot_name, overwrite=overwrite, extra_args=extra_args
        )
        assert isinstance(ss_name, str)  # Guaranteed since background=False
        return ss_name

    def __init_snapshot_from_io(self, name, fd):
        # type: (str, IO) -> None
        json_data = workhelper.get_data_upload_snapshot(self, name, fd)
        resthelper.get_json_response(
            self, CoordConsts.SVC_RSC_UPLOAD_SNAPSHOT, json_data
        )

    def __init_snapshot_from_file(self, name, file_to_send):
        # type: (str, str) -> None
        tmp_file_name = None  # type: Optional[Text]
        if os.path.isdir(file_to_send):
            # delete=False because we re-open for reading
            with tempfile.NamedTemporaryFile(delete=False) as temp_zip_file:
                zip_dir(file_to_send, temp_zip_file)
                tmp_file_name = file_to_send = temp_zip_file.name
        elif os.path.isfile(file_to_send):
            if not zipfile.is_zipfile(file_to_send):
                raise ValueError("{} is not a valid zip file".format(file_to_send))

        with open(file_to_send, "rb") as fd:
            self.__init_snapshot_from_io(name, fd)

        # Cleanup tmp file if we made one
        if tmp_file_name is not None:
            try:
                os.remove(tmp_file_name)
            except (OSError, IOError):
                # If we can't delete the file for some reason, let it be,
                # no need to crash initialization
                pass

    def _init_snapshot(
        self, upload, name=None, overwrite=False, background=False, extra_args=None
    ):
        # type: (Union[str, IO], Optional[str], bool, bool, Optional[Dict[str, Any]]) -> Union[str, Dict[str, str]]
        if self.network is None:
            self.set_network()

        if name is None:
            name = Options.default_snapshot_prefix + get_uuid()
        validate_name(name)

        if name in self.list_snapshots():
            if overwrite:
                self.delete_snapshot(name)
            else:
                raise ValueError(
                    "A snapshot named "
                    "{}"
                    " already exists in network "
                    "{}"
                    ". "
                    "Use overwrite = True if you want to overwrite the "
                    "existing snapshot".format(name, self.network)
                )

        if isinstance(upload, str):
            self.__init_snapshot_from_file(name, upload)
        else:
            if not zipfile.is_zipfile(upload):
                raise ValueError("The provided data is not a valid zip file")
            # upload is an IO-like object already
            self.__init_snapshot_from_io(name, upload)

        return self._parse_snapshot(name, background, extra_args)

    def list_networks(self):
        # type: () -> List[str]
        """
        List networks the session's API key can access.

        :return: network names
        :rtype: list
        """
        return [d["name"] for d in restv2helper.list_networks(self)]

    def list_incomplete_works(self):
        # type: () -> Dict[str, Any]
        """
        Get pending work that is incomplete.

        :return: JSON dictionary of question name to question object
        :rtype: dict
        """
        json_data = workhelper.get_data_list_incomplete_work(self)
        response = resthelper.get_json_response(
            self, CoordConsts.SVC_RSC_LIST_INCOMPLETE_WORK, json_data
        )
        return response

    def list_snapshots(self, verbose=False):
        # type: (bool) -> Union[List[str], List[Dict[str,Any]]]
        """
        List snapshots for the current network.

        :param verbose: If true, return the full output of Batfish, including
            snapshot metadata.
        :type verbose: bool

        :return: snapshot names or the full JSON response containing snapshots
            and metadata (if `verbose=True`)
        :rtype: list
        """
        return restv2helper.list_snapshots(self, verbose)

    def put_reference_book(self, book):
        # type: (ReferenceBook) -> None
        """
        Put a reference book in the active network.

        If a book with the same name exists, it is overwritten.

        :param book: The ReferenceBook object to add
        :type book: :class:`~pybatfish.datamodel.referencelibrary.ReferenceBook`
        """
        restv2helper.put_reference_book(self, book)

    def put_node_role_dimension(self, dimension):
        # type: (NodeRoleDimension) -> None
        """
        Put a role dimension in the active network.

        Overwrites the old dimension if one of the same name already exists.

        Individual role dimension mappings within the dimension must have a valid (java) regex.

        :param dimension: The NodeRoleDimension object for the dimension to add
        :type dimension: :class:`~pybatfish.datamodel.referencelibrary.NodeRoleDimension`
        """
        restv2helper.put_node_role_dimension(self, dimension)

    def put_node_roles(self, node_roles_data):
        # type: (NodeRolesData) -> None
        """
        Writes the definitions of node roles for the active network. Completely replaces any existing definitions.

        :param node_roles_data: node roles definitions to add to the active network
        :type node_roles_data: :class:`~pybatfish.datamodel.referencelibrary.NodeRolesData`
        """
        restv2helper.put_node_roles(self, node_roles_data)

    def set_network(
        self, name: Optional[str] = None, prefix: str = Options.default_network_prefix
    ) -> str:
        """
        Configure the network used for analysis.

        :param name: name of the network to set. If `None`, a name will be generated
        :type name: str
        :param prefix: prefix to prepend to auto-generated network names if name is empty
        :type name: str

        :return: name of the configured network
        :rtype: str
        :raises BatfishException: if configuration fails
        """
        if name is None:
            name = prefix + get_uuid()
        validate_name(name, "network")

        try:
            net = restv2helper.get_network(self, name)
            self.network = str(net["name"])
            return self.network
        except HTTPError as e:
            if e.response.status_code != 404:
                raise BatfishException("Unknown error accessing network", e)

        json_data = workhelper.get_data_init_network(self, name)
        json_response = resthelper.get_json_response(
            self, CoordConsts.SVC_RSC_INIT_NETWORK, json_data
        )

        network_name = json_response.get(CoordConsts.SVC_KEY_NETWORK_NAME)
        if network_name is None:
            raise BatfishException(
                "Network initialization failed. Server response: {}".format(
                    json_response
                )
            )

        self.network = str(network_name)
        return self.network

    def set_snapshot(self, name=None, index=None):
        # type: (Optional[str], Optional[int]) -> str
        """
        Set the current snapshot by name or index.

        :param name: name of the snapshot to set as the current snapshot
        :type name: str
        :param index: set the current snapshot to the ``index``-th most recent snapshot
        :type index: int

        :return: the name of the successfully set snapshot
        :rtype: str
        """
        if name is None and index is None:
            raise ValueError("One of name and index must be set")
        if name is not None and index is not None:
            raise ValueError("Only one of name and index can be set")

        snapshots = self.list_snapshots()

        # Index specified, simply give the ith snapshot
        if index is not None:
            if not (-len(snapshots) <= index < len(snapshots)):
                raise IndexError(
                    "Server has only {} snapshots: {}".format(len(snapshots), snapshots)
                )
            self.snapshot = str(snapshots[index])

        # Name specified, make sure it exists.
        else:
            assert name is not None  # type-hint to Python
            if name not in snapshots:
                raise ValueError(
                    "No snapshot named "
                    "{}"
                    " was found in network "
                    "{}"
                    ": {}".format(name, self.network, snapshots)
                )
            self.snapshot = name

        logging.getLogger(__name__).info(
            "Default snapshot is now set to %s", self.snapshot
        )
        return self.snapshot

    def upload_diagnostics(
        self,
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
        :type netconan_config: str
        :param contact_info: optional contact info associated with this upload
        :type contact_info: str
        :param proxy: a proxy URL to use when uploading data.
        :return: location of anonymized files (local directory if doing dry run, otherwise upload ID)
        :rtype: str
        """
        metadata = {}
        if contact_info:
            metadata["contact_info"] = contact_info
        return upload_diagnostics(
            self,
            metadata=metadata,
            dry_run=dry_run,
            netconan_config=netconan_config,
            proxy=proxy,
        )

    def validate_facts(self, expected_facts, snapshot=None):
        # type: (Text, Optional[Text]) -> Dict[Text, Any]
        """
        Return a dictionary of mismatched facts between the loaded expected facts and the actual facts.

        :param expected_facts: path to directory to read expected fact YAML files from
        :type expected_facts: Text
        :param snapshot: name of the snapshot to validate facts for, defaults to the current snapshot
        :type snapshot: Text
        :return: facts about the specified nodes on the current network snapshot
        :rtype: dict
        """
        actual_facts = get_facts(self, snapshot=snapshot)
        expected_facts_ = load_facts(expected_facts)
        return validate_facts(expected_facts_, actual_facts)

    def _check_network(self):
        """Check if current network is set."""
        if self.network is None:
            raise ValueError("Network is not set")

    def _check_snapshot(self):
        """Check if current snapshot (and network) is set."""
        self._check_network()
        if self.snapshot is None:
            raise ValueError("Snapshot is not set")

    def _parse_snapshot(self, name, background, extra_args):
        # type: (str, bool, Optional[Dict[str, Any]]) -> Union[str, Dict[str, str]]
        """
        Parse specified snapshot.

        :param name: name of the snapshot to initialize
        :type name: str
        :param background: whether or not to run the task in the background
        :type background: bool
        :param extra_args: extra arguments to be passed to the parse command.
        :type extra_args: dict

        :return: name of initialized snapshot, or JSON dictionary of task status if background=True
        :rtype: Union[str, Dict]
        """
        work_item = workhelper.get_workitem_parse(self, name)
        answer_dict = workhelper.execute(
            work_item, self, background=background, extra_args=extra_args
        )
        if background:
            self.snapshot = name
            return answer_dict

        status = WorkStatusCode(answer_dict["status"])

        if status != WorkStatusCode.TERMINATEDNORMALLY:
            init_log = restv2helper.get_work_log(self, name, work_item.id)
            raise BatfishException(
                "Initializing snapshot {ss} failed with status {status}\n{log}".format(
                    ss=name, status=status, log=init_log
                )
            )
        else:
            self.snapshot = name
            logging.getLogger(__name__).info(
                "Default snapshot is now set to %s", self.snapshot
            )
            if self.enable_diagnostics:
                warn_on_snapshot_failure(self)

            return self.snapshot


def _text_with_platform(text, platform):
    # type: (str, Optional[str]) -> str
    """Returns the text with platform prepended if needed."""
    if platform is None:
        return text
    p = platform.strip().lower()
    return "!RANCID-CONTENT-TYPE: {}\n{}".format(p, text)


def _create_in_memory_zip(text, filename, platform):
    # type: (str, str, Optional[str]) -> IO
    """Creates an in-memory zip file for a single file snapshot."""
    from io import BytesIO

    data = BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED, False) as zf:
        zipfilename = os.path.join("snapshot", "configs", filename)
        zf.writestr(zipfilename, _text_with_platform(text, platform))
    return data
