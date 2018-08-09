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

from pybatfish.datamodel.aspath import AsPath
from pybatfish.datamodel.ip import Ip
from pybatfish.datamodel.node import Node
from pybatfish.datamodel.prefix import Prefix


class BgpAdvertisement(object):

    def __init__(self, dictionary):
        self.asPath = AsPath(dictionary["asPath"])
        self.dstIp = Ip(dictionary["dstIp"])
        self.dstNode = Node(dict(name=dictionary["dstNode"]))
        self.dstVrf = dictionary["dstVrf"]
        self.localPreference = dictionary["localPreference"]
        self.med = dictionary["med"]
        self.network = Prefix(dictionary["network"])
        self.nextHopIp = Ip(dictionary["nextHopIp"])
        self.originType = dictionary["originType"]
        self.originatorIp = Ip(dictionary["originatorIp"])
        self.srcIp = Ip(dictionary["srcIp"])
        self.srcNode = Node(dict(name=dictionary["srcNode"]))
        self.srcProtocol = dictionary["srcProtocol"]
        self.srcVrf = dictionary["srcVrf"]
        self.type = dictionary["type"]
        self.weight = dictionary["weight"]

    def __repr__(self):
        return str(self)

    def __str__(self):
        # skipping the other fields for now
        return '{}<-{}: {} {})'.format(self.dstNode, self.srcNode, self.network,
                                       self.asPath)
