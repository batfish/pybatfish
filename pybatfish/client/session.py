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

from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
import zipfile
from io import SEEK_CUR, SEEK_SET
from typing import (  # noqa: F401
    IO,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Text,
    Tuple,
    Union,
)

from requests import HTTPError

from pybatfish.client import restv2helper, workhelper
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
from pybatfish.client.workhelper import get_work_status
from pybatfish.datamodel import (
    AutoCompleteSuggestion,
    HeaderConstraints,
    Interface,
    NodeRolesData,
    ReferenceBook,
    ReferenceLibrary,
    VariableType,
)
from pybatfish.datamodel.answer import Answer, TableAnswer  # noqa: F401
from pybatfish.datamodel.answer.table import is_table_ans
from pybatfish.exception import BatfishException
from pybatfish.question.question import Questions
from pybatfish.util import get_uuid, validate_name, zip_dir

from .options import Options


class Asserts:
    """Class containing assertions for a given Session."""

    def __init__(self, session):
        self.session = session

    def assert_filter_denies(
        self,
        filters: str,
        headers: HeaderConstraints,
        startLocation: str | None = None,
        soft: bool = False,
        snapshot: str | None = None,
        df_format: str = "table",
    ) -> bool:
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
        self,
        filters: str,
        soft: bool = False,
        snapshot: str | None = None,
        df_format: str = "table",
    ) -> bool:
        """
        Check that a filter (e.g. an ACL) has no unreachable lines.

        A filter line is considered unreachable if it will never match a packet,
        e.g., because its match condition is empty or covered completely by those of
        prior lines.

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
        filters: str,
        headers: HeaderConstraints,
        startLocation: str | None = None,
        soft: bool = False,
        snapshot: str | None = None,
        df_format: str = "table",
    ) -> bool:
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
        self,
        startLocation: str,
        headers: HeaderConstraints,
        soft: bool = False,
        snapshot: str | None = None,
        df_format: str = "table",
    ) -> bool:
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
        self,
        startLocation: str,
        headers: HeaderConstraints,
        soft: bool = False,
        snapshot: str | None = None,
        df_format: str = "table",
    ) -> bool:
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
        self,
        snapshot: str | None = None,
        nodes: str | None = None,
        protocols: list[str] | None = None,
        soft: bool = False,
        df_format: str = "table",
        ignore_same_node: bool = False,
    ) -> bool:
        """Assert that there are no duplicate router IDs present in the snapshot.

        :param snapshot: the snapshot on which to check the assertion
        :param nodes: the nodes on which to run the assertion
        :param protocols: the protocol on which to use the assertion, e.g. bgp, ospf, etc.
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        :param ignore_same_node: whether to ignore duplicate router-ids on the same node.
        """
        return assert_no_duplicate_router_ids(
            snapshot,
            nodes,
            protocols,
            soft,
            self.session,
            df_format,
            ignore_same_node,
        )

    def assert_no_forwarding_loops(
        self,
        snapshot: str | None = None,
        soft: bool = False,
        df_format: str = "table",
    ) -> bool:
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
        nodes: str | None = None,
        remote_nodes: str | None = None,
        status: str | None = None,
        snapshot: str | None = None,
        soft: bool = False,
        df_format: str = "table",
    ) -> bool:
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
        nodes: str | None = None,
        remote_nodes: str | None = None,
        snapshot: str | None = None,
        soft: bool = False,
        df_format: str = "table",
    ) -> bool:
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
        nodes: str | None = None,
        remote_nodes: str | None = None,
        snapshot: str | None = None,
        soft: bool = False,
        df_format: str = "table",
    ) -> bool:
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
        self,
        snapshot: str | None = None,
        soft: bool = False,
        df_format: str = "table",
    ) -> bool:
        """Assert that there are no undefined references present in the snapshot.

        :param snapshot: the snapshot on which to check the assertion
        :param soft: whether this assertion is soft (i.e., generates a warning but
            not a failure)
        :param df_format: How to format the Dataframe content in the output message.
            Valid options are 'table' and 'records' (each row is a key-value pairs).
        """
        return assert_no_undefined_references(snapshot, soft, self.session, df_format)


class Session:
    """Keeps session configuration needed to connect to a Batfish server.

    :ivar host: The host of the batfish service
    :ivar port: The port batfish service is running on (9996 by default if not set)
    :ivar port_v2: Legacy alias for port
    :ivar ssl: Whether to use SSL when connecting to Batfish (False by default)
    :ivar api_key: Your API key
    """

    def __init__(
        self,
        host: str = Options.coordinator_host,
        port: Optional[int] = None,
        # port v1 is deprecated
        port_v1: int = Options.coordinator_work_port,
        # port v2 is a backwards-compatible, but deprecated alias for port
        port_v2: Optional[int] = None,
        ssl: bool = Options.use_ssl,
        verify_ssl_certs: bool = Options.verify_ssl_certs,
        api_key: str = CoordConsts.DEFAULT_API_KEY,
        load_questions: bool = True,
    ):
        # Coordinator args
        self.host: str = host
        if port is not None:
            self.port_v2 = port
        elif port_v2 is not None:
            self.port_v2 = port_v2
        else:
            self.port_v2 = Options.coordinator_work_v2_port
        self._base_uri_v2: str = CoordConsts.SVC_CFG_WORK_MGR2
        self.ssl: bool = ssl
        self.verify_ssl_certs: bool = verify_ssl_certs

        # Session args
        self.api_key: str = api_key
        self.network: str | None = None
        self.snapshot: str | None = None

        # Objects to hold and manage questions and asserts
        self.q = Questions(self)
        self.asserts = Asserts(self)

        # Additional worker args
        self.additional_args: dict = {}

        self.elapsed_delay: int = 5
        self.stale_timeout: int = 5

        # Auto-load question templates
        if load_questions:
            self.q.load()

    @classmethod
    def get_session_types(cls) -> dict[str, Callable]:
        """Get a dict of possible session types mapping their names to session classes."""
        import sys
        from importlib.metadata import entry_points

        if sys.version_info < (3, 10):
            eps = entry_points().get("batfish_session", [])
        else:
            eps = entry_points(group="batfish_session")
        return {ep.name: ep.load() for ep in eps}

    @classmethod
    def get(cls, type_: str = "bf", **params: Any) -> Session:
        """Instantiate and return a Session object of the specified type with the specified params."""
        sessions = cls.get_session_types()
        session_module = sessions.get(type_)
        if session_module is None:
            raise ValueError(
                "Invalid session type. Specified type '{}' does not match any registered session type: {}".format(
                    type_, set(sessions.keys())
                )
            )
        session: Session = session_module(**params)
        return session

    def _get_bf_version(self) -> str:
        """Get the Batfish backend version."""
        bf_version = self.get_component_versions().get("Batfish")
        if not bf_version:
            raise BatfishException("backend did not return a version for 'Batfish'")
        return str(bf_version)

    def delete_network(self, name: str) -> None:
        """
        Delete network by name.

        :param name: name of the network to delete
        :type name: str
        """
        if name is None:
            raise ValueError("Network to be deleted must be supplied")
        restv2helper.delete_network(self, name)

    def delete_network_object(self, key: str) -> None:
        """Deletes the network object with specified key."""
        restv2helper.delete_network_object(self, key)

    def delete_node_role_dimension(self, dimension: str) -> None:
        """
        Deletes the definition of the given role dimension for the active network.

        :param dimension: name of the dimension to delete
        :type dimension: str
        """
        restv2helper.delete_node_role_dimension(self, dimension)

    def delete_reference_book(self, name: str) -> None:
        """
        Deletes the reference book with the specified name for the active network.

        :param name: name of the reference book to delete
        :type name: str
        """
        restv2helper.delete_reference_book(self, name)

    def delete_snapshot(self, name: str) -> None:
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

    def delete_snapshot_object(self, key: str, snapshot: Optional[str] = None) -> None:
        """Deletes the snapshot object with specified key."""
        restv2helper.delete_snapshot_object(self, key, snapshot)

    def extract_facts(
        self,
        nodes: str = "/.*/",
        output_directory: str | None = None,
        snapshot: str | None = None,
    ) -> dict[str, Any]:
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
        base_name: str,
        name: str | None = None,
        overwrite: bool = False,
        deactivate_interfaces: list[Interface] | None = None,
        deactivate_nodes: list[str] | None = None,
        restore_interfaces: list[Interface] | None = None,
        restore_nodes: list[str] | None = None,
        add_files: str | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> str | None:
        """
        Copy an existing snapshot and deactivate or reactivate specified interfaces, nodes, and links on the copy.

        :param base_name: name of the snapshot to copy
        :type base_name: str
        :param name: name of the snapshot to initialize
        :type name: str
        :param overwrite: whether to overwrite an existing snapshot with the
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
        :param extra_args: extra arguments to control snapshot processing:
           1) "ignoremanagementinterfaces" (bool) -- whether to shut management interfaces (default is True);
           2) "parsereuse" (bool) -- whether to reuse parsing work from prior snapshots when file content is identical (default is True)
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
        base_name: str,
        name: str | None = None,
        overwrite: bool = False,
        background: bool = False,
        deactivate_interfaces: list[Interface] | None = None,
        deactivate_nodes: list[str] | None = None,
        restore_interfaces: list[Interface] | None = None,
        restore_nodes: list[str] | None = None,
        add_files: str | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> str | dict | None:
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

    def generate_dataplane(
        self,
        snapshot: str | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> str:
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

    def get_answer(
        self, question: str, snapshot: str, reference_snapshot: str | None = None
    ) -> Answer:
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

    def get_base_url2(self) -> str:
        """Generate the base URL for V2 of the coordinator APIs."""
        protocol = "https" if self.ssl else "http"
        return "{}://{}:{}{}".format(
            protocol, self.host, self.port_v2, self._base_uri_v2
        )

    def get_network_object_stream(self, key: str) -> Any:
        """Returns a binary stream of the content of the network object with specified key."""
        return restv2helper.get_network_object(self, key)

    def get_network_object_text(self, key: str, encoding: str = "utf-8") -> str:
        """Returns the text content of the network object with specified key."""
        with self.get_network_object_stream(key) as stream:
            ret: str = stream.read().decode(encoding)
            return ret

    def get_node_roles(self, inferred: bool = False) -> NodeRolesData:
        """
        Returns the definitions of node roles for the active network or inferred roles for the active snapshot.

        :param inferred: whether to fetch the active snapshot's inferred node roles
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

    def get_reference_book(self, name: str) -> ReferenceBook:
        """
        Returns the specified reference book for the active network.

        :param name: name of the reference book to fetch
        :type name: str
        """
        return ReferenceBook.from_dict(restv2helper.get_reference_book(self, name))

    def get_reference_library(self) -> ReferenceLibrary:
        """Returns the reference library for the active network."""
        return ReferenceLibrary.from_dict(restv2helper.get_reference_library(self))

    def get_snapshot(self, snapshot: str | str | None = None) -> str:
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
                "set_snapshot (e.g. bf.set_snapshot('NAME')"
            )

    def get_snapshot_input_object_stream(
        self, key: str, snapshot: Optional[str] = None
    ) -> Any:
        """Returns a binary stream of the content of the snapshot input object with specified key."""
        return restv2helper.get_snapshot_input_object(self, key, snapshot)

    def get_snapshot_input_object_text(
        self, key: str, encoding: str = "utf-8", snapshot: Optional[str] = None
    ) -> str:
        """Returns the text content of the snapshot input object with specified key."""
        with self.get_snapshot_input_object_stream(key, snapshot) as stream:
            ret: str = stream.read().decode(encoding)
            return ret

    def get_snapshot_object_stream(
        self, key: str, snapshot: Optional[str] = None
    ) -> Any:
        """Returns a binary stream of the content of the snapshot object with specified key."""
        return restv2helper.get_snapshot_object(self, key, snapshot)

    def get_snapshot_object_text(
        self, key: str, encoding: str = "utf-8", snapshot: Optional[str] = None
    ) -> str:
        """Returns the text content of the snapshot object with specified key."""
        with self.get_snapshot_object_stream(key, snapshot) as stream:
            ret: str = stream.read().decode(encoding)
            return ret

    def get_work_status(self, work_item):
        """Get the status for the specified work item."""
        self._check_network()
        return get_work_status(work_item, self)

    def get_component_versions(self) -> dict[str, Any]:
        """Get a dictionary of backend components (e.g. Batfish, Z3) and their versions."""
        return restv2helper.get_component_versions(self)

    def init_snapshot(
        self,
        upload: str,
        name: str | None = None,
        overwrite: bool = False,
        extra_args: dict[str, Any] | None = None,
    ) -> str:
        """
        Initialize a new snapshot.

        :param upload: path to the snapshot zip or directory
        :type upload: str
        :param name: name of the snapshot to initialize
        :type name: str
        :param overwrite: whether to overwrite an existing snapshot with the
           same name
        :type overwrite: bool
        :param extra_args: extra arguments to control snapshot processing:
           1) "ignoremanagementinterfaces" (bool) -- whether to shut management interfaces (default is True);
           2) "parsereuse" (bool) -- whether to reuse parsing work from prior snapshots when file content is identical (default is True)
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
        text: str,
        filename: str | None = None,
        snapshot_name: str | None = None,
        platform: str | None = None,
        overwrite: bool = False,
        extra_args: dict[str, Any] | None = None,
    ) -> str:
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
        :param overwrite: whether to overwrite an existing snapshot with
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

    def __init_snapshot_from_io(self, name: str, fd: IO) -> None:
        restv2helper.upload_snapshot(self, name, fd)

    def __init_snapshot_from_file(self, name: str, file_to_send: str) -> None:
        tmp_file_name: str | None = None
        if os.path.isdir(file_to_send):
            # delete=False because we re-open for reading
            with tempfile.NamedTemporaryFile(delete=False) as temp_zip_file:
                zip_dir(file_to_send, temp_zip_file)
                tmp_file_name = file_to_send = temp_zip_file.name
        elif os.path.isfile(file_to_send):
            if not zipfile.is_zipfile(file_to_send):
                raise ValueError(f"{file_to_send} is not a valid zip file")

        with open(file_to_send, "rb") as fd:
            self.__init_snapshot_from_io(name, fd)

        # Cleanup tmp file if we made one
        if tmp_file_name is not None:
            try:
                os.remove(tmp_file_name)
            except OSError:
                # If we can't delete the file for some reason, let it be,
                # no need to crash initialization
                pass

    def _init_snapshot(
        self,
        upload: str | IO,
        name: str | None = None,
        overwrite: bool = False,
        background: bool = False,
        extra_args: dict[str, Any] | None = None,
    ) -> str | dict[str, str]:
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
            seekable = (
                hasattr(upload, "seek")
                and hasattr(upload, "seekable")
                and upload.seekable()
            )
            if (
                seekable
            ):  # else assume it's a zipfile, and rely on backend to say otherwise
                old_pos = upload.seek(0, SEEK_CUR)
                if not zipfile.is_zipfile(upload):
                    raise ValueError("The provided data is not a valid zip file")
                upload.seek(old_pos, SEEK_SET)
            # upload is an IO-like object already
            self.__init_snapshot_from_io(name, upload)

        return self._parse_snapshot(name, background, extra_args)

    def list_networks(self) -> list[str]:
        """
        List networks the session's API key can access.

        :return: network names
        :rtype: list
        """
        return [d["name"] for d in restv2helper.list_networks(self)]

    def list_incomplete_works(self) -> dict[str, Any]:
        """
        Get pending work that is incomplete.

        :return: JSON dictionary of question name to question object
        :rtype: dict
        """
        self._check_network()
        statuses = restv2helper.list_incomplete_work(self)
        return {CoordConsts.SVC_KEY_WORK_LIST: json.dumps(statuses)}

    def list_snapshots(self, verbose: bool = False) -> list[str] | list[dict[str, Any]]:
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

    def put_reference_book(self, book: ReferenceBook) -> None:
        """
        Put a reference book in the active network.

        If a book with the same name exists, it is overwritten.

        :param book: The ReferenceBook object to add
        :type book: :class:`~pybatfish.datamodel.referencelibrary.ReferenceBook`
        """
        restv2helper.put_reference_book(self, book)

    def put_network_object(self, key: str, data: Any) -> None:
        """Puts data as the network object with specified key."""
        restv2helper.put_network_object(self, key, data)

    def put_node_roles(self, node_roles_data: NodeRolesData) -> None:
        """
        Writes the definitions of node roles for the active network. Completely replaces any existing definitions.

        :param node_roles_data: node roles definitions to add to the active network
        :type node_roles_data: :class:`~pybatfish.datamodel.referencelibrary.NodeRolesData`
        """
        restv2helper.put_node_roles(self, node_roles_data)

    def put_snapshot_object(self, key: str, data: Any) -> None:
        """Puts data as the snapshot object with specified key."""
        restv2helper.put_snapshot_object(self, key, data, self.snapshot)

    def set_network(
        self, name: str | None = None, prefix: str = Options.default_network_prefix
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
            if e.response is None or e.response.status_code != 404:
                raise BatfishException("Unknown error accessing network", e)

        restv2helper.init_network(self, name)
        self.network = str(name)
        return self.network

    def set_snapshot(self, name: str | None = None, index: int | None = None) -> str:
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
                    f"Server has only {len(snapshots)} snapshots: {snapshots}"
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

    def validate_facts(
        self, expected_facts: str, snapshot: str | None = None
    ) -> dict[str, Any]:
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

    def _parse_snapshot(
        self, name: str, background: bool, extra_args: dict[str, Any] | None
    ) -> str | dict[str, str]:
        """
        Parse specified snapshot.

        :param name: name of the snapshot to initialize
        :type name: str
        :param background: whether to run the task in the background
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
        self.snapshot = name
        logging.getLogger(__name__).info(
            "Default snapshot is now set to %s", self.snapshot
        )
        return self.snapshot

    def auto_complete(
        self,
        completion_type: VariableType,
        query: str,
        max_suggestions: int | None = None,
    ) -> list[AutoCompleteSuggestion]:
        """
        Get a list of autocomplete suggestions that match the provided query based on the variable type.

        If completion is not supported for the provided variable type a BatfishException will be raised.

        Usage Example::

            >>> from pybatfish.client.session import Session
            >>> from pybatfish.datamodel.primitives import AutoCompleteSuggestion, VariableType
            >>> bf = Session.get('bf')
            >>> name = bf.set_network()
            >>> bf.auto_complete(VariableType.ROUTING_PROTOCOL_SPEC, "b") # doctest: +SKIP
            [AutoCompleteSuggestion(description=None, insertion_index=0, is_partial=False, rank=2147483647, text='bgp'),
                AutoCompleteSuggestion(description=None, insertion_index=0, is_partial=False, rank=2147483647, text='ebgp'),
                AutoCompleteSuggestion(description=None, insertion_index=0, is_partial=False, rank=2147483647, text='ibgp')]

        :param completion_type: The type of parameter to suggest autocompletions for
        :type completion_type: :class:`~pybatfish.datamodel.primitives.VariableType`
        :param query: The partial string to match suggestions on
        :type query: str
        :param max_suggestions: Optional max number of suggestions to be returned. 0 is treated as no limit.
        :type max_suggestions: int
        """
        if max_suggestions and max_suggestions < 0:
            raise ValueError("max_suggestions cannot be negative")
        self._check_network()
        response = restv2helper.auto_complete(
            self, completion_type, query, max_suggestions
        )
        results = [
            AutoCompleteSuggestion.from_dict(suggestion)
            for suggestion in response.get(CoordConsts.SVC_KEY_SUGGESTIONS, [])
        ]
        # TODO: Should instead reject if snapshot is not set but variable type requires a snapshot
        if not results and not self.snapshot:
            logging.getLogger(__name__).warning(
                "No results, but snapshot is not set. You might get results if you first call <session>.set_snapshot"
            )
        return results


def _text_with_platform(text: str, platform: str | None) -> str:
    """Returns the text with platform prepended if needed."""
    if platform is None:
        return text
    p = platform.strip().lower()
    return f"!RANCID-CONTENT-TYPE: {p}\n{text}"


def _create_in_memory_zip(text: str, filename: str, platform: str | None) -> IO:
    """Creates an in-memory zip file for a single file snapshot."""
    from io import BytesIO

    data = BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED, False) as zf:
        zipfilename = os.path.join("snapshot", "configs", filename)
        zf.writestr(zipfilename, _text_with_platform(text, platform))
    # rewind after writing
    data.seek(0, SEEK_SET)
    return data


def _version_to_tuple(version: str) -> tuple[int, ...]:
    """Convert version string N(.N)* to a tuple of ints."""
    return tuple(int(i) for i in version.split("."))


def _version_less_than(version: tuple[int, ...], min_version: tuple[int, ...]) -> bool:
    """
    Check if specified version is less than the specified min version.

    Assumed dev versions start with a 0.
    """
    # Assume the dev version starts with a 0
    if version[0] != 0:
        return version < min_version
    # Dev version is considered newer than any version
    return False
