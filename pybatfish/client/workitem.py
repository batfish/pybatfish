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

import json
from typing import Dict, Optional, TYPE_CHECKING  # noqa: F401

import pybatfish.util as batfishutils

if TYPE_CHECKING:
    from pybatfish.client.session import Session  # noqa: F401


class WorkItem(object):
    """
    A class representing a Batfish task.

    This file mirrors WorkItem.java in the batfish-common-protocol module.
    """

    def __init__(self, session):
        # type: (Session) -> None
        self.id = batfishutils.get_uuid()  # type: str
        self.network = session.network  # type: Optional[str]
        self.requestParams = dict(session.additional_args)  # type: Dict

    def to_json(self):
        # type: () -> str
        params = {
            "containerName": self.network,
            "id": self.id,
            "requestParams": self.requestParams,
        }
        trName = self.requestParams.get("testrig")
        if trName is not None:
            params["testrigName"] = trName
        return json.dumps(params)
