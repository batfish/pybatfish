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
import json
import logging
import os
import tempfile
from typing import (Any, Dict, List, Optional,  # noqa: F401
                    Text, Union)

from deprecated import deprecated
from requests import HTTPError

from pybatfish.client import resthelper, restv2helper, workhelper
from pybatfish.client._diagnostics import (upload_diagnostics,
                                           warn_on_snapshot_failure)
from pybatfish.client.consts import CoordConsts, WorkStatusCode
from pybatfish.client.workhelper import get_work_status
from pybatfish.datamodel import (Edge, Interface, NodeRoleDimension,
                                 NodeRolesData, ReferenceBook,
                                 ReferenceLibrary)
from pybatfish.exception import BatfishException
from pybatfish.question.question import (Questions)
from pybatfish.util import get_uuid, validate_name, zip_dir
from .options import Options


class Session(object):
    """Keeps session configuration needed to connect to a Batfish server.

    :ivar host: The host of the batfish service
    :ivar port_v1: The port batfish service is running on (9997 by default)
    :ivar port_v2: The additional port of batfish service (9996 by default)
    :ivar ssl: Whether to use SSL when connecting to Batfish (False by default)
    :ivar api_key: Your API key
    """

    def __init__(self, host=Options.coordinator_host,
                 port_v1=Options.coordinator_work_port,
                 port_v2=Options.coordinator_work_v2_port,
                 ssl=Options.use_ssl,
                 verify_ssl_certs=Options.verify_ssl_certs,
                 load_questions=True):
        # type: (Text, int, int, bool, bool, bool) -> None
        # Coordinator args
        self.host = host  # type: Text
        self.port_v1 = port_v1  # type: int
        self._base_uri_v1 = CoordConsts.SVC_CFG_WORK_MGR  # type: str
        self.port_v2 = port_v2  # type: int
        self._base_uri_v2 = CoordConsts.SVC_CFG_WORK_MGR2  # type: str
        self.ssl = ssl  # type: bool
        self.verify_ssl_certs = verify_ssl_certs  # type: bool

        # Session args
        self.api_key = CoordConsts.DEFAULT_API_KEY  # type: str
        self.network = None  # type: Optional[str]
        self.snapshot = None  # type: Optional[str]

        # Object to hold and manage questions
        self.q = Questions(self)

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

    def delete_network(self, name):
        # type: (str) -> None
        """
        Delete network by name.

        :param name: name of the network to delete
        :type name: str
        """
        if name is None:
            raise ValueError('Network to be deleted must be supplied')
        json_data = workhelper.get_data_delete_network(self, name)
        resthelper.get_json_response(self,
                                     CoordConsts.SVC_RSC_DEL_NETWORK,
                                     json_data)

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
        if name is None:
            raise ValueError('Snapshot to be deleted must be supplied')
        json_data = workhelper.get_data_delete_snapshot(self, name)
        resthelper.get_json_response(self,
                                     CoordConsts.SVC_RSC_DEL_SNAPSHOT,
                                     json_data)

    def fork_snapshot(self, base_name, name=None, overwrite=False,
                      deactivate_interfaces=None, deactivate_links=None,
                      deactivate_nodes=None, restore_interfaces=None,
                      restore_links=None, restore_nodes=None, add_files=None,
                      extra_args=None):
        # type: (str, Optional[str], bool, Optional[List[Interface]], Optional[List[Edge]], Optional[List[str]], Optional[List[Interface]], Optional[List[Edge]], Optional[List[str]], Optional[str], Optional[Dict[str, Any]]) -> Optional[str]
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
        :param extra_args: extra arguments to be passed to the parse command.
        :type extra_args: dict

        :return: name of initialized snapshot or None if the call fails
        :rtype: Optional[str]
        """
        result = self._fork_snapshot(base_name, name=name, overwrite=overwrite,
                                     deactivate_interfaces=deactivate_interfaces,
                                     deactivate_links=deactivate_links,
                                     deactivate_nodes=deactivate_nodes,
                                     restore_interfaces=restore_interfaces,
                                     restore_links=restore_links,
                                     restore_nodes=restore_nodes,
                                     add_files=add_files,
                                     extra_args=extra_args)
        # Get around mypy thinking this could also be Dict
        # We know the result here will be str or None because background = False
        if isinstance(result, str):
            return result
        return None

    def _fork_snapshot(self, base_name, name=None, overwrite=False,
                       background=False, deactivate_interfaces=None,
                       deactivate_links=None, deactivate_nodes=None,
                       restore_interfaces=None, restore_links=None,
                       restore_nodes=None, add_files=None,
                       extra_args=None):
        # type: (str, Optional[str], bool, bool, Optional[List[Interface]], Optional[List[Edge]], Optional[List[str]], Optional[List[Interface]], Optional[List[Edge]], Optional[List[str]], Optional[str], Optional[Dict[str, Any]]) -> Union[str, Dict, None]
        self._check_network()

        if name is None:
            name = Options.default_snapshot_prefix + get_uuid()
        validate_name(name)

        if name in self.list_snapshots():
            if overwrite:
                self.delete_snapshot(name)
            else:
                raise ValueError(
                    'A snapshot named ''{}'' already exists in network ''{}'''.format(
                        name, self.network))

        encoded_file = None
        if add_files is not None:
            file_to_send = add_files
            if os.path.isdir(add_files):
                temp_zip_file = tempfile.NamedTemporaryFile()
                zip_dir(add_files, temp_zip_file)
                file_to_send = temp_zip_file.name

            if os.path.isfile(file_to_send):
                with open(file_to_send, "rb") as f:
                    encoded_file = base64.b64encode(f.read()).decode(
                        'ascii')

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

        work_item = workhelper.get_workitem_generate_dataplane(self,
                                                               snapshot)
        answer_dict = workhelper.execute(work_item, self,
                                         extra_args=extra_args)
        return str(answer_dict["status"].value)

    def get_answer(self, question, snapshot, reference_snapshot=None):
        # type: (str, str, Optional[str]) -> Any
        """
        Get the answer for a previously asked question.

        :param question: the unique identifier of the previously asked question
        :type question: str
        :param snapshot: name of the snapshot the question was run on
        :type snapshot: str
        :param reference_snapshot: if present, gets the answer for a differential question asked against the specified reference snapshot
        :type reference_snapshot: str
        """
        json_data = workhelper.get_data_get_answer(self, question,
                                                   snapshot,
                                                   reference_snapshot)
        response = resthelper.get_json_response(self,
                                                CoordConsts.SVC_RSC_GET_ANSWER,
                                                json_data)
        return json.loads(response["answer"])

    def get_base_url(self):
        # type: () -> str
        """Generate the base URL for connecting to Batfish coordinator."""
        protocol = "https" if self.ssl else "http"
        return '{0}://{1}:{2}{3}'.format(protocol, self.host,
                                         self.port_v1,
                                         self._base_uri_v1)

    def get_base_url2(self):
        # type: () -> str
        """Generate the base URL for V2 of the coordinator APIs."""
        protocol = "https" if self.ssl else "http"
        return '{0}://{1}:{2}{3}'.format(protocol, self.host,
                                         self.port_v2,
                                         self._base_uri_v2)

    def get_info(self):
        # type: () -> Dict[str, Any]
        """Get basic info about the Batfish service (including name, version, ...)."""
        return resthelper.get_json_response(self, '', useHttpGet=True)

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
                restv2helper.get_snapshot_inferred_node_role_dimension(
                    self,
                    dimension))
        return NodeRoleDimension.from_dict(
            restv2helper.get_node_role_dimension(self, dimension))

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
                restv2helper.get_snapshot_inferred_node_roles(self))
        return NodeRolesData.from_dict(restv2helper.get_node_roles(self))

    def get_reference_book(self, name):
        # type: (str) -> ReferenceBook
        """
        Returns the specified reference book for the active network.

        :param name: name of the reference book to fetch
        :type name: str
        """
        return ReferenceBook.from_dict(
            restv2helper.get_reference_book(self, name))

    def get_reference_library(self):
        # type: () -> ReferenceLibrary
        """Returns the reference library for the active network."""
        return ReferenceLibrary.from_dict(
            restv2helper.get_reference_library(self))

    def get_snapshot(self, snapshot=None):
        # type: (Optional[str]) -> str
        """
        Get the specified or active snapshot name.

        :param snapshot: if specified, this name is returned instead of active snapshot
        :type snapshot: str

        :return: name of the active snapshot, or the specified snapshot if applicable
        :rtype: str

        :raises ValueError: if there is no active snapshot and no snapshot was specified
        """
        if snapshot is not None:
            return snapshot
        elif self.snapshot is not None:
            return self.snapshot
        else:
            raise ValueError(
                "snapshot must be either provided or set using "
                "set_snapshot (e.g. bf_session.set_snapshot('NAME')")

    def get_url(self, resource):
        # type: (str) -> str
        """
        Get URL for the specified resource.

        :param resource: URI of the requested resource
        :type resource: str
        """
        return '{0}/{1}'.format(self.get_base_url(), resource)

    def get_work_status(self, work_item):
        """Get the status for the specified work item."""
        return get_work_status(work_item, self)

    def init_snapshot(self, upload, name=None, overwrite=False,
                      extra_args=None):
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
        ss_name = self._init_snapshot(upload, name=name,
                                      overwrite=overwrite,
                                      extra_args=extra_args)
        assert isinstance(ss_name, str)  # Guaranteed since background=False
        return ss_name

    def init_snapshot_from_text(
            self, text, filename='config', snapshot_name=None, platform=None,
            overwrite=False, extra_args=None):
        # type: (str, str, Optional[str], Optional[str], bool, Optional[Dict[str, Any]]) -> str
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
            i.e., "cisco-nx", "arista", "f5", or "cisco-xr" for the above examples.
            See https://www.shrubbery.net/rancid/man/router.db.5.html .
        :type snapshot_name: str
        :param overwrite: whether or not to overwrite an existing snapshot with the
           same name
        :type overwrite: bool
        :param extra_args: extra arguments to be passed to the parse command
        :type extra_args: dict

        :return: name of initialized snapshot
        :rtype: str
        """
        import tempfile

        d = tempfile.TemporaryDirectory(prefix='_batfish_temp.')
        try:
            _create_single_file_zip(d.name, text, filename, platform)
            ss_name = self._init_snapshot(d.name, name=snapshot_name,
                                          overwrite=overwrite,
                                          extra_args=extra_args)
            assert isinstance(ss_name, str)  # Guaranteed since background=False
            return ss_name
        finally:
            d.cleanup()

    def _init_snapshot(self, upload, name=None, overwrite=False,
                       background=False,
                       extra_args=None):
        # type: (str, Optional[str], bool, bool, Optional[Dict[str, Any]]) -> Union[str, Dict[str, str]]
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
                    'A snapshot named ''{}'' already exists in network ''{}'''.format(
                        name, self.network))

        file_to_send = upload
        if os.path.isdir(upload):
            temp_zip_file = tempfile.NamedTemporaryFile()
            zip_dir(upload, temp_zip_file)
            file_to_send = temp_zip_file.name

        json_data = workhelper.get_data_upload_snapshot(self, name,
                                                        file_to_send)
        resthelper.get_json_response(self,
                                     CoordConsts.SVC_RSC_UPLOAD_SNAPSHOT,
                                     json_data)

        return self._parse_snapshot(name, background, extra_args)

    def list_networks(self):
        # type: () -> List[str]
        """
        List networks the session's API key can access.

        :return: network names
        :rtype: list
        """
        json_data = workhelper.get_data_list_networks(self)
        json_response = resthelper.get_json_response(
            self, CoordConsts.SVC_RSC_LIST_NETWORKS, json_data)

        return list(map(str, json_response['networklist']))

    def list_incomplete_works(self):
        # type: () -> Dict[str, Any]
        """
        Get pending work that is incomplete.

        :return: JSON dictionary of question name to question object
        :rtype: dict
        """
        json_data = workhelper.get_data_list_incomplete_work(self)
        response = resthelper.get_json_response(self,
                                                CoordConsts.SVC_RSC_LIST_INCOMPLETE_WORK,
                                                json_data)
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

        Individual roles within the dimension must have a valid (java) regex.
        The node list within those roles, if present, is ignored by the server.

        :param dimension: The NodeRoleDimension object for the dimension to add
        :type dimension: :class:`~pybatfish.datamodel.referencelibrary.NodeRoleDimension`
        """
        if dimension.type == "AUTO":
            raise ValueError("Cannot put a dimension of type AUTO")
        restv2helper.put_node_role_dimension(self, dimension)

    def put_node_roles(self, node_roles_data):
        # type: (NodeRolesData) -> None
        """
        Writes the definitions of node roles for the active network. Completely replaces any existing definitions.

        :param node_roles_data: node roles definitions to add to the active network
        :type node_roles_data: :class:`~pybatfish.datamodel.referencelibrary.NodeRolesData`
        """
        restv2helper.put_node_roles(self, node_roles_data)

    def set_network(self, name=None, prefix=Options.default_network_prefix):
        # type: (str, str) -> str
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
            self.network = str(net['name'])
            return self.network
        except HTTPError as e:
            if e.response.status_code != 404:
                raise BatfishException('Unknown error accessing network', e)

        json_data = workhelper.get_data_init_network(self, name)
        json_response = resthelper.get_json_response(
            self, CoordConsts.SVC_RSC_INIT_NETWORK, json_data)

        network_name = json_response.get(CoordConsts.SVC_KEY_NETWORK_NAME)
        if network_name is None:
            raise BatfishException(
                "Network initialization failed. Server response: {}".format(
                    json_response))

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
            raise ValueError('One of name and index must be set')
        if name is not None and index is not None:
            raise ValueError('Only one of name and index can be set')

        snapshots = self.list_snapshots()

        # Index specified, simply give the ith snapshot
        if index is not None:
            if not (-len(snapshots) <= index < len(snapshots)):
                raise IndexError(
                    "Server has only {} snapshots: {}".format(
                        len(snapshots), snapshots))
            self.snapshot = str(snapshots[index])

        # Name specified, make sure it exists.
        else:
            assert name is not None  # type-hint to Python
            if name not in snapshots:
                raise ValueError(
                    'No snapshot named ''{}'' was found in network ''{}'': {}'.format(
                        name, self.network, snapshots))
            self.snapshot = name

        logging.getLogger(__name__).info(
            "Default snapshot is now set to %s",
            self.snapshot)
        return self.snapshot

    def upload_diagnostics(self, dry_run=True, netconan_config=None,
                           contact_info=None):
        # type: (bool, str, Optional[str]) -> str
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

        :param dry_run: whether or not to skip upload; if False, anonymized files will be stored locally, otherwise anonymized files will be uploaded to Batfish developers
        :type dry_run: bool
        :param netconan_config: path to Netconan configuration file
        :type netconan_config: str
        :param contact_info: optional contact info associated with this upload
        :type contact_info: str
        :return: location of anonymized files (local directory if doing dry run, otherwise upload ID)
        :rtype: str
        """
        metadata = {}
        if contact_info:
            metadata['contact_info'] = contact_info
        return upload_diagnostics(self, metadata=metadata, dry_run=dry_run,
                                  netconan_config=netconan_config)

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
        answer_dict = workhelper.execute(work_item, self,
                                         background=background,
                                         extra_args=extra_args)
        if background:
            self.snapshot = name
            return answer_dict

        status = WorkStatusCode(answer_dict["status"])

        if status != WorkStatusCode.TERMINATEDNORMALLY:
            init_log = restv2helper.get_work_log(self, name, work_item.id)
            raise BatfishException(
                'Initializing snapshot {ss} failed with status {status}\n{log}'.format(
                    ss=name, status=status, log=init_log))
        else:
            self.snapshot = name
            logging.getLogger(__name__).info(
                "Default snapshot is now set to %s",
                self.snapshot)
            if self.enable_diagnostics:
                warn_on_snapshot_failure(self)

            return self.snapshot


def _create_single_file_zip(dirname, text, filename, platform):
    # type: (str, str, str, Optional[str]) -> None
    """Utility function for Session.init_snapshot_from_text."""
    configs = os.path.join(dirname, 'configs')
    config_file = os.path.join(configs, filename)
    os.makedirs(configs)
    with open(config_file, 'w') as outfile:
        if platform is not None:
            p = platform.strip().lower()
            outfile.write('!RANCID-CONTENT-TYPE: {}\n'.format(p))
        outfile.write(text)
