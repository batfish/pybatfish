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
from typing import Dict, List  # noqa: F401

import attr

from pybatfish.datamodel.primitives import DataModelElement

__all__ = ["BgpRoute", "BgpRouteDiff", "BgpRouteDiffs"]


@attr.s(frozen=True)
class BgpRoute(DataModelElement):
    """A BGP routing advertisement.

    :ivar network: The network prefix advertised by the route.
    :ivar asPath: The AS path of the route.
    :ivar communities: The communities of the route.
    :ivar localPreference: The local preference of the route.
    :ivar metric: The metric of the route.
    :ivar originatorIp: The IP address of the originator of the route.
    :ivar originType: The origin type of the route.
    :ivar sourceProtocol: The source protocol of the route.
    """

    network = attr.ib(type=str)
    originatorIp = attr.ib(type=str)
    originType = attr.ib(type=str)
    protocol = attr.ib(type=str)
    asPath = attr.ib(type=list, default=[])
    communities = attr.ib(type=list, default=[])
    localPreference = attr.ib(type=int, default=0)
    metric = attr.ib(type=int, default=0)
    sourceProtocol = attr.ib(type=str, default=None)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> BgpRoute
        return BgpRoute(
            json_dict["network"],
            json_dict["originatorIp"],
            json_dict["originType"],
            json_dict["protocol"],
            json_dict.get("asPath", []),
            json_dict.get("communities", []),
            json_dict.get("localPreference", 0),
            json_dict.get("metric", 0),
            json_dict.get("srcProtocol", None),
        )

    def dict(self):
        # type: () -> Dict
        return {
            # needed for batfish jackson deserialization
            "class": "org.batfish.datamodel.BgpRoute",
            "network": self.network,
            "asPath": self.asPath,
            "communities": self.communities,
            "localPreference": self.localPreference,
            "metric": self.metric,
            "originatorIp": self.originatorIp,
            "originType": self.originType,
            "protocol": self.protocol,
            "srcProtocol": self.sourceProtocol,
        }

    def _repr_html_(self):
        # type: () -> str
        return "<br>".join(self._repr_html_lines())

    def _repr_html_lines(self):
        # type: () -> List[str]
        lines = []
        lines.append("Network: {node}".format(node=self.network))
        lines.append("AS Path: %s" % self.asPath)
        lines.append("Communities: %s" % self.communities)
        lines.append("Local Preference: %s" % self.localPreference)
        lines.append("Metric: %s" % self.metric)
        lines.append("Originator IP: %s" % self.originatorIp)
        lines.append("Origin Type: %s" % self.originType)
        lines.append("Protocol: %s" % self.protocol)
        lines.append("Source Protocol: %s" % self.sourceProtocol)
        return lines


@attr.s(frozen=True)
class BgpRouteDiff(DataModelElement):
    """A difference between two BGP routes.

    :ivar fieldName: A Flow field name that has changed.
    :ivar oldValue: The old value of the field.
    :ivar newValue: The new value of the field.
    """

    fieldName = attr.ib(type=str)
    oldValue = attr.ib(type=str)
    newValue = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> BgpRouteDiff
        return BgpRouteDiff(
            json_dict["fieldName"], json_dict["oldValue"], json_dict["newValue"]
        )

    def _repr_html_(self):
        # type: () -> str
        return "{fieldName}: {oldValue} -> {newValue}".format(
            fieldName=self.fieldName, oldValue=self.oldValue, newValue=self.newValue
        )


@attr.s(frozen=True)
class BgpRouteDiffs(DataModelElement):
    """A set of differences between two BGP routes.

    :ivar diffs: The set of BgpRouteDiff objects.
    """

    diffs = attr.ib(type=List[BgpRouteDiff])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> BgpRouteDiffs
        return BgpRouteDiffs(
            [
                BgpRouteDiff.from_dict(route_dict)
                for route_dict in json_dict.get("diffs", [])
            ]
        )

    def _repr_html_(self):
        # type: () -> str
        return "<br>".join(diff._repr_html_() for diff in self.diffs)
