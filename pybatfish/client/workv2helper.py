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
"""A collection of functions that execute RPCs against a Batfish server."""

from __future__ import absolute_import, print_function

from pybatfish.client.consts import CoordConstsV2


def get_data_fork_snapshot(base_name, deactivate_interfaces,
                           deactivate_links, deactivate_nodes):
    json_data = {CoordConstsV2.KEY_SNAPSHOT_BASE: base_name,
                 CoordConstsV2.KEY_DEACTIVATE_INTERFACES: deactivate_interfaces,
                 CoordConstsV2.KEY_DEACTIVATE_LINKS: deactivate_links,
                 CoordConstsV2.KEY_DEACTIVATE_NODES: deactivate_nodes}
    return json_data
