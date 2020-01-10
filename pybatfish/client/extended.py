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


def bf_delete_network_object(key):
    # type: (Text) -> None
    """Deletes the network object with specified key."""
    return restv2helper.delete_network_object(bf_session, key)


def bf_delete_snapshot_object(key, snapshot=None):
    # type: (str, Optional[str]) -> None
    """Deletes the snapshot object with specified key."""
    restv2helper.delete_snapshot_object(bf_session, key, snapshot)


def bf_get_network_object_stream(key):
    # type: (Text) -> Any
    """Returns a binary stream of the content of the network object with specified key."""
    return restv2helper.get_network_object(bf_session, key)


def bf_get_network_object_text(key, encoding="utf-8"):
    # type: (Text, Text) -> str
    """Returns the text content of the network object with specified key."""
    with bf_get_network_object_stream(key) as stream:
        text = stream.read().decode(encoding)
    return str(text)


def bf_get_snapshot_input_object_stream(key, snapshot=None):
    # type: (Text, Optional[Text]) -> Any
    """Returns a binary stream of the content of the snapshot input object with specified key."""
    return restv2helper.get_snapshot_input_object(bf_session, key, snapshot)


def bf_get_snapshot_input_object_text(key, encoding="utf-8", snapshot=None):
    # type: (Text, Text, Optional[Text]) -> Text
    """Returns the text content of the snapshot input object with specified key."""
    with bf_get_snapshot_input_object_stream(key, snapshot) as stream:
        text = stream.read().decode(encoding)
    return str(text)


def bf_get_snapshot_object_stream(key, snapshot=None):
    # type: (Text, Optional[Text]) -> Any
    """Returns a binary stream of the content of the snapshot object with specified key."""
    return restv2helper.get_snapshot_object(bf_session, key, snapshot)


def bf_get_snapshot_object_text(key, encoding="utf-8", snapshot=None):
    # type: (Text, Text, Optional[Text]) -> Text
    """Returns the text content of the snapshot object with specified key."""
    with bf_get_snapshot_object_stream(key, snapshot) as stream:
        text = stream.read().decode(encoding)
    return str(text)


def bf_put_network_object(key, data):
    # type: (Text, Any) -> None
    """Puts data as the network object with specified key."""
    restv2helper.put_network_object(bf_session, key, data)


def bf_put_snapshot_object(key, data, snapshot=None):
    # type: (Text, Any, Optional[Text]) -> None
    """Puts data as the snapshot object with specified key."""
    restv2helper.put_snapshot_object(bf_session, key, data, snapshot)
