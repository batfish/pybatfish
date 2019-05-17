# coding utf-8
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
"""Internal representation for validation commands."""
from abc import ABCMeta
from typing import List, Optional

from six import add_metaclass


@add_metaclass(ABCMeta)
class Command(object):
    """Command abstract class."""


class InitSnapshot(Command):
    """Command to initialize a new snapshot."""

    def __init__(self, name, upload, overwrite):
        # type: (str, Optional[str], bool) -> None
        self.name = name
        self.upload = upload
        self.overwrite = overwrite


class SetNetwork(Command):
    """Command to set current network."""

    def __init__(self, name):
        # type: (str) -> None
        self.name = name


class ShowFacts(Command):
    """Command to show facts about a network."""

    def __init__(self, nodes=None):
        # type: (str) -> None
        self.nodes = nodes


class CommandList(object):
    """Internal representation of a collection of commands."""

    def __init__(self, name, cmds):
        # type: (str, List[Command]) -> None
        self.name = name
        self.cmds = cmds
