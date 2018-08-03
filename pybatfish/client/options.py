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

from pybatfish.client.consts import CoordConsts


class Options(object):
    """Global options for pybatfish."""

    coordinator_host = "localhost"  # type: str
    coordinator_work_port = CoordConsts.SVC_CFG_WORK_PORT  # type: int
    coordinator_work_v2_port = CoordConsts.SVC_CFG_WORK_V2_PORT  # type: int
    use_ssl = not CoordConsts.SVC_CFG_WORK_SSL_DISABLE  # type: bool
    # This should only be false for local testing
    verify_ssl_certs = True  # type: bool

    default_network_prefix = "pcp"  # type: str
    default_delta_env_prefix = "env_"  # type: str
    default_question_prefix = "q"  # type: str
    default_snapshot_prefix = "ss_"  # type: str

    max_tries_to_connect_to_coordinator = 5  # type: int
    num_tries_warn_threshold = 5  # type: int
    request_backoff_factor = 0.8  # type: float
    seconds_to_sleep_between_tries_to_coordinator = 3  # type: int
