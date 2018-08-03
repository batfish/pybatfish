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

from pybatfish.datamodel.bgpadvertisement import BgpAdvertisement
from pybatfish.datamodel.edge import Edge
from pybatfish.datamodel.interface import Interface
from pybatfish.datamodel.node import Node
from pybatfish.util import conditional_str


class Environment:
    def __init__(self, dictionary):
        self.envName = dictionary["envName"]
        self.testrigName = dictionary["testrigName"]
        self.edgeBlackList = [Edge(edge) for edge in
                              dictionary.get("edgeBlacklist", [])]
        self.interfaceBlackList = [Interface(interface) for interface in
                                   dictionary.get("interfaceBlacklist", [])]
        self.nodeBlackList = [Node({"name": nodeName}) for nodeName in
                              dictionary.get("nodeBlacklist", [])]
        self.bgpTables = dictionary.get("bgpTables", {})
        self.routingTables = dictionary.get("routingTables", {})
        self.externalBgpAnnouncements = [BgpAdvertisement(advert) for advert in
                                         dictionary.get(
                                             "externalBgpAnnouncements", [])]

    def __str__(self):
        retStrHead = "{} environment for {}".format(self.envName,
                                                    self.testrigName)
        retStrTail = "{}{}{}{}{}{}".format(
            conditional_str("  edgeBlacklist: ", self.edgeBlackList, "\n"),
            conditional_str("  interfaceBlacklist: ", self.interfaceBlackList,
                            "\n"),
            conditional_str("  nodeBlacklist: ", self.nodeBlackList, "\n"),
            conditional_str("  bgpTables: ", self.bgpTables, "\n"),
            conditional_str("  routingTables: ", self.routingTables, "\n"),
            conditional_str("  externalAnnouncements: ",
                            self.externalBgpAnnouncements, "\n"))
        retStrTail = retStrTail if retStrTail != "" else "  None\n"
        return retStrHead + "\n" + retStrTail
