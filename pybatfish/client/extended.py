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
from .commands import (bf_session, restv2helper)

__all__ = ['bf_delete_network_object',
           'bf_get_network_object_stream',
           'bf_get_network_object_text',
           'bf_get_snapshot_input_object_stream',
           'bf_get_snapshot_input_object_text',
           'bf_get_snapshot_object_stream',
           'bf_get_snapshot_object_text',
           'bf_put_network_object',
           'bf_put_snapshot_object']


def bf_delete_network_object(key):
    # type: (str) -> None
    """Deletes the network object with specified key."""
    return restv2helper.delete_network_object(bf_session, key)


def bf_get_network_object_stream(key):
    # type: (str) -> Any
    """Returns a binary stream of the content of the network object with specified key."""
    return restv2helper.get_network_object(bf_session, key)


def bf_get_network_object_text(key, encoding='utf-8'):
    # type: (str, str) -> str
    """Returns the text content of the network object with specified key."""
    with bf_get_network_object_stream(key) as stream:
        text = stream.read().decode(encoding)
    return str(text)


def bf_get_snapshot_input_object_stream(key, snapshot=None):
    # type: (str, Optional[str]) -> Any
    """Returns a binary stream of the content of the snapshot input object with specified key."""
    return restv2helper.get_snapshot_input_object(bf_session, key, snapshot)


def bf_get_snapshot_input_object_text(key, encoding='utf-8', snapshot=None):
    # type: (str, str, Optional[str]) -> str
    """Returns the text content of the snapshot input object with specified key."""
    with bf_get_snapshot_input_object_stream(key, snapshot) as stream:
        text = stream.read().decode(encoding)
    return str(text)


def bf_get_snapshot_object_stream(key, snapshot=None):
    # type: (Text, Optional[Text]) -> Any
    """Returns a binary stream of the content of the snapshot object with specified key."""
    return restv2helper.get_snapshot_object(bf_session, key, snapshot)


def bf_get_snapshot_object_text(key, encoding='utf-8', snapshot=None):
    # type: (str, str, Optional[str]) -> str
    """Returns the text content of the snapshot object with specified key."""
    with bf_get_snapshot_object_stream(key, snapshot) as stream:
        text = stream.read().decode(encoding)
    return str(text)


def bf_put_network_object(key, data):
    # type: (str, Any) -> None
    """Puts data as the network object with specified key."""
    restv2helper.put_network_object(bf_session, key, data)


def bf_put_snapshot_object(key, data, snapshot=None):
    # type: (Text, Any, Optional[Text]) -> None
    """Puts data as the snapshot object with specified key."""
    restv2helper.put_snapshot_object(bf_session, key, data, snapshot)


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
    json_data = workhelper.get_data_sync_snapshots_sync_now(
        bf_session, plugin, force)
    json_response = resthelper.get_json_response(
        bf_session, CoordConsts.SVC_RSC_SYNC_SNAPSHOTS_SYNC_NOW, json_data)
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
        bf_session, plugin, settings)
    json_response = resthelper.get_json_response(
        bf_session, CoordConsts.SVC_RSC_SYNC_SNAPSHOTS_UPDATE_SETTINGS,
        json_data)
    return json_response
