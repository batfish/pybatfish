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

from pybatfish.datamodel.edge import Edge
from pybatfish.datamodel.flow import Flow


class FlowTraceHop:
    def __init__(self, dictionary):
        self.edge = Edge(dictionary["edge"])
        self.routes = list(dictionary.get("routes", []))
        transformed_flow = dictionary.get("transformedFlow")
        self.transformedFlow = Flow(transformed_flow) if transformed_flow else None

    def __str__(self):
        return str(self.edge) + " " + str(self.routes) + \
            (("\n  --> transformedFlow: " + str(self.transformedFlow)) if self.transformedFlow else "")
