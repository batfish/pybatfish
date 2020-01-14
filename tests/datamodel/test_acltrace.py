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

import pytest

from pybatfish.datamodel.acl import AclTrace, TraceNode


# test if an acl trace is deserialized properly
def test_acl_trace_deserialization():
    trace_dict = {"events": [{"description": "aa"}, {"description": "bb"}]}

    # check deserialization
    acl_trace = AclTrace.from_dict(trace_dict)
    assert len(acl_trace.events) == 2

    # check stringification works
    str(acl_trace)


def test_trace_node_no_children():
    trace_node_dict = {
        "traceElement": {"fragments": [{"class": "TextFragment", "text": "aaa"}],},
    }
    trace_node = TraceNode.from_dict(trace_node_dict)
    assert len(trace_node.children) == 0
    assert str(trace_node) == "aaa"
    assert trace_node._repr_html_() == "aaa"


def test_trace_node_with_children():
    trace_node_dict = {
        "traceElement": {"fragments": [{"class": "TextFragment", "text": "aaa"}],},
        "children": [
            {
                "traceElement": {
                    "fragments": [{"class": "TextFragment", "text": "bbb"},]
                },
            },
            {
                "traceElement": {
                    "fragments": [{"class": "TextFragment", "text": "ccc"},]
                },
            },
        ],
    }
    trace_node = TraceNode.from_dict(trace_node_dict)
    assert len(trace_node.children) == 2
    assert str(trace_node) == "\n".join(["aaa", "  - bbb", "  - ccc",])
    html_text = trace_node._repr_html_()
    assert "aaa" in html_text
    assert "<li>bbb</li>" in html_text
    assert "<li>ccc</li>" in html_text


def test_trace_node_nested_children():
    trace_node_dict = {
        "traceElement": {"fragments": [{"class": "TextFragment", "text": "aaa"}],},
        "children": [
            {
                "traceElement": {
                    "fragments": [{"class": "TextFragment", "text": "bbb"},]
                },
                "children": [
                    {
                        "traceElement": {
                            "fragments": [{"class": "TextFragment", "text": "ccc"}]
                        }
                    }
                ],
            },
            {
                "traceElement": {
                    "fragments": [{"class": "TextFragment", "text": "ddd"},]
                },
            },
        ],
    }
    trace_node = TraceNode.from_dict(trace_node_dict)
    assert len(trace_node.children) == 2
    assert len(trace_node.children[0].children) == 1
    assert str(trace_node) == "\n".join(["aaa", "  - bbb", "    - ccc", "  - ddd",])
    html_text = trace_node._repr_html_()
    assert "aaa" in html_text
    assert "<li>bbb <ul>" in html_text
    assert "<ul><li>ccc</li></ul>" in html_text
    assert "<li>ddd</li>" in html_text


if __name__ == "__main__":
    pytest.main()
