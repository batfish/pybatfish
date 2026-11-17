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

from pybatfish.client.consts import CoordConsts


class Options:
    """Global options for pybatfish."""

    coordinator_host: str = "localhost"
    coordinator_work_port: int = CoordConsts.SVC_CFG_WORK_PORT
    coordinator_work_v2_port: int = CoordConsts.SVC_CFG_WORK_V2_PORT
    use_ssl: bool = not CoordConsts.SVC_CFG_WORK_SSL_DISABLE
    # This should only be false for local testing
    verify_ssl_certs: bool = True

    default_network_prefix: str = "pcp"
    default_question_prefix: str = "q"
    default_snapshot_prefix: str = "ss_"

    # Parameters for urllib3.Retry, see docs there for more info
    #
    # Read as "try" "time to sleep if this fails" "total sleep so far"
    #
    # >>> s = 0
    # >>> for i in range(10):
    # ...    cur = min(2**i * 0.8, 120)
    # ...    print(f'{i} {cur} {s}')
    # ...    s += cur
    # ...
    # 0 0.8 0
    # 1 1.6 0.8
    # 2 3.2 2.4000000000000004
    # 3 6.4 5.6000000000000005
    # 4 12.8 12.0
    # 5 25.6 24.8
    # 6 51.2 50.400000000000006
    # 7 102.4 101.60000000000001
    # 8 120 204.0
    # 9 120 324.0   # This sleep of 120s will never happen, would fail instead
    #
    request_backoff_factor: float = 0.8
    # Number of tries to connect to coordinator initially
    # We should fail fast initially in case connection is misconfigured
    max_initial_tries_to_connect_to_coordinator: int = 3
    # Number of tries to communicate with coordinator after session setup
    # We should be forgiving if coordinator is unresponsive after setting up
    # a connection (e.g. GC)
    max_retries_to_connect_to_coordinator: int = 10
