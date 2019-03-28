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
from typing import Dict, Optional  # noqa: F401

from deprecated import deprecated

from pybatfish.client.consts import CoordConsts
from .options import Options


class Session(object):
    """Keeps session configuration needed to connect to a Batfish server.

    :ivar host: The host of the batfish service
    :ivar port_v1: The port batfish service is running on (9997 by default)
    :ivar port_v2: The additional port of batfish service (9996 by default)
    :ivar ssl: Whether to use SSL when connecting to Batfish (False by default)
    :ivar api_key: Your API key
    """

    def __init__(self, logger, host=Options.coordinator_host,
                 port_v1=Options.coordinator_work_port,
                 port_v2=Options.coordinator_work_v2_port,
                 ssl=Options.use_ssl,
                 verify_ssl_certs=Options.verify_ssl_certs):
        # type: (Logger, str, int, int, bool, bool) -> None
        # Coordinator args
        self.host = host  # type: str
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

        # Additional worker args
        self.additional_args = {}  # type: Dict

        self.logger = logger  # type: Logger

        self.elapsed_delay = 5  # type: int
        self.stale_timeout = 5  # type: int
        self.enable_diagnostics = True  # type: bool

    # Support old property names
    @property
    @deprecated(reason="Use additional_args")
    def additionalArgs(self):
        return self.additional_args

    @additionalArgs.setter
    @deprecated(reason="Use additional_args")
    def additionalArgs(self, val):
        self.additional_args = val

    @property
    @deprecated(reason="Use api_key")
    def apiKey(self):
        return self.api_key

    @apiKey.setter
    @deprecated(reason="Use api_key")
    def apiKey(self, val):
        self.api_key = val

    @property
    @deprecated(reason="Use snapshot")
    def baseSnapshot(self):
        return self.snapshot

    @baseSnapshot.setter
    @deprecated(reason="Use snapshot")
    def baseSnapshot(self, val):
        self.snapshot = val

    @property
    @deprecated(reason="Use port_v1")
    def coordinatorPort(self):
        return self.port_v1

    @coordinatorPort.setter
    @deprecated(reason="Use port_v1")
    def coordinatorPort(self, val):
        self.port_v1 = val

    @property
    @deprecated(reason="Use port_v2")
    def coordinatorPort2(self):
        return self.port_v2

    @coordinatorPort2.setter
    @deprecated(reason="Use port_v2")
    def coordinatorPort2(self, val):
        self.port_v2 = val

    @property
    @deprecated(reason="Use ssl")
    def useSsl(self):
        return self.ssl

    @useSsl.setter
    @deprecated(reason="Use ssl")
    def useSsl(self, val):
        self.ssl = val

    @property
    @deprecated(reason="Use verify_ssl_certs")
    def verifySslCerts(self):
        return self.verify_ssl_certs

    @verifySslCerts.setter
    @deprecated(reason="Use verify_ssl_certs")
    def verifySslCerts(self, val):
        self.verify_ssl_certs = val

    def get_base_url(self):
        # type: () -> str
        """Generate the base URL for connecting to batfish coordinator."""
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

    def get_url(self, resource):
        # type: (str) -> str
        return '{0}/{1}'.format(self.get_base_url(), resource)

    def get_snapshot(self, snapshot=None):
        # type: (Optional[str]) -> str
        if snapshot is not None:
            return snapshot
        elif self.snapshot is not None:
            return self.snapshot
        else:
            raise ValueError(
                "snapshot must be either provided or set using bf_set_snapshot")
