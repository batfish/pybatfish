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
"""Contains Batfish extended client commands for devs and power users that query the Batfish service."""

from __future__ import absolute_import, print_function

from typing import Any, Optional, Text  # noqa: F401

from pybatfish.client import resthelper, workhelper
from pybatfish.client.consts import CoordConsts
from pybatfish.client.session import Session
from pybatfish.util import first_non_none
from .commands import bf_session, restv2helper

__all__ = [
    "bf_delete_network_object",
    "bf_delete_snapshot_object",
    "bf_get_network_object_stream",
    "bf_get_network_object_text",
    "bf_get_snapshot_input_object_stream",
    "bf_get_snapshot_input_object_text",
    "bf_get_snapshot_object_stream",
    "bf_get_snapshot_object_text",
    "bf_put_network_object",
    "bf_put_snapshot_object",
]


def bf_delete_network_object(key: Text, session: Optional[Session] = None) -> None:
    """Deletes the network object with specified key."""
    return restv2helper.delete_network_object(
        first_non_none((session, bf_session)), key
    )


def bf_delete_snapshot_object(
    key: str, snapshot: Optional[str] = None, session: Optional[Session] = None
) -> None:
    """Deletes the snapshot object with specified key."""
    restv2helper.delete_snapshot_object(
        first_non_none((session, bf_session)), key, snapshot
    )


def bf_get_network_object_stream(key: str, session: Optional[Session] = None):
    """Returns a binary stream of the content of the network object with specified key."""
    return restv2helper.get_network_object(first_non_none((session, bf_session)), key)


def bf_get_network_object_text(
    key: str, encoding: str = "utf-8", session: Optional[Session] = None
):
    """Returns the text content of the network object with specified key."""
    with bf_get_network_object_stream(key, session=session) as stream:
        text = stream.read().decode(encoding)
    return str(text)


def bf_get_snapshot_input_object_stream(
    key: str, snapshot: Optional[str] = None, session: Optional[Session] = None
):
    """Returns a binary stream of the content of the snapshot input object with specified key."""
    return restv2helper.get_snapshot_input_object(
        first_non_none((session, bf_session)), key, snapshot
    )


def bf_get_snapshot_input_object_text(
    key: str,
    encoding: str = "utf-8",
    snapshot: Optional[str] = None,
    session: Optional[Session] = None,
):
    """Returns the text content of the snapshot input object with specified key."""
    with bf_get_snapshot_input_object_stream(
        key, snapshot=snapshot, session=session
    ) as stream:
        text = stream.read().decode(encoding)
    return str(text)


def bf_get_snapshot_object_stream(
    key: str, snapshot: Optional[str] = None, session: Optional[Session] = None
):
    """Returns a binary stream of the content of the snapshot object with specified key."""
    return restv2helper.get_snapshot_object(
        first_non_none((session, bf_session)), key, snapshot
    )


def bf_get_snapshot_object_text(
    key: str,
    encoding: str = "utf-8",
    snapshot: Optional[str] = None,
    session: Optional[Session] = None,
):
    """Returns the text content of the snapshot object with specified key."""
    with bf_get_snapshot_object_stream(
        key, snapshot=snapshot, session=session
    ) as stream:
        text = stream.read().decode(encoding)
    return str(text)


def bf_put_network_object(key: str, data: Any, session: Optional[Session] = None):
    """Puts data as the network object with specified key."""
    restv2helper.put_network_object(first_non_none((session, bf_session)), key, data)


def bf_put_snapshot_object(
    key: str,
    data: Any,
    snapshot: Optional[str] = None,
    session: Optional[Session] = None,
):
    """Puts data as the snapshot object with specified key."""
    restv2helper.put_snapshot_object(
        first_non_none((session, bf_session)), key, data, snapshot
    )


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
    json_data = workhelper.get_data_sync_snapshots_sync_now(bf_session, plugin, force)
    json_response = resthelper.get_json_response(
        bf_session, CoordConsts.SVC_RSC_SYNC_SNAPSHOTS_SYNC_NOW, json_data
    )
    return json_response


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
    json_data = workhelper.get_data_sync_snapshots_update_settings(
        bf_session, plugin, settings
    )
    json_response = resthelper.get_json_response(
        bf_session, CoordConsts.SVC_RSC_SYNC_SNAPSHOTS_UPDATE_SETTINGS, json_data
    )
    return json_response
