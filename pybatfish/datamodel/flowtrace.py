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

from pybatfish.datamodel.flowtracehop import FlowTraceHop


class FlowTrace:

    def __init__(self, dictionary):
        self.disposition = dictionary["disposition"]
        self.flowTraceHops = [FlowTraceHop(hop) for hop in
                              dictionary.get("hops", [])]
        self.notes = dictionary["notes"]

    def __repr__(self):
        return str(self)

    def __str__(self):
        ret_str = ""
        for hop_num, hop in enumerate(self.flowTraceHops):
            ret_str += "{} {}\n".format(hop_num + 1, hop)
        ret_str += "{}\n".format(self.notes)
        return ret_str
