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

from logging import Logger  # noqa: F401
from typing import Dict, List, Optional  # noqa: F401

from pybatfish.client.consts import CoordConsts
from .options import Options


class Session(object):
    """Keeps session configuration needed to connect to a Batfish server."""

    def __init__(self, logger):
        # type: (Logger) -> None
        # Coordinator args
        self.coordinatorHost = Options.coordinator_host  # type: str
        self.coordinatorPort = Options.coordinator_work_port  # type: int
        self.coordinatorBase = CoordConsts.SVC_CFG_WORK_MGR  # type: str
        self.coordinatorPort2 = Options.coordinator_work_v2_port  # type: int
        self.coordinatorBase2 = CoordConsts.SVC_CFG_WORK_MGR2  # type: str
        self.useSsl = Options.use_ssl  # type: bool
        self.verifySslCerts = Options.verify_ssl_certs  # type: bool

        # Session args
        self.apiKey = CoordConsts.DEFAULT_API_KEY  # type: str
        self.network = None  # type: Optional[str]
        self.baseSnapshot = None  # type: Optional[str]

        # Additional worker args
        self.additionalArgs = {}  # type: Dict

        self.logger = logger  # type: Logger

        self.elapsed_delay = 5  # type: int
        self.stale_timeout = 5  # type: int

        # cache _baseUrl
        self._base_url = self.get_base_url()  # type: str

    def get_base_url(self):
        # type: () -> str
        """Generate the base URL for connecting to batfish coordinator."""
        protocol = "https" if self.useSsl else "http"
        return '{0}://{1}:{2}{3}'.format(protocol, self.coordinatorHost,
                                         self.coordinatorPort,
                                         self.coordinatorBase)

    def get_base_url2(self):
        # type: () -> str
        """Generate the base URL for V2 of the coordinator APIs."""
        protocol = "https" if self.useSsl else "http"
        return '{0}://{1}:{2}{3}'.format(protocol, self.coordinatorHost,
                                         self.coordinatorPort2,
                                         self.coordinatorBase2)

    def get_url(self, resource):
        # type: (str) -> str
        return '{0}/{1}'.format(self.get_base_url(), resource)

    def get_snapshot(self, snapshot=None):
        # type: (Optional[str]) -> str
        if snapshot is not None:
            return snapshot
        elif self.baseSnapshot is not None:
            return self.baseSnapshot
        else:
            raise ValueError(
                "snapshot must be either provided or set using bf_set_snapshot")
