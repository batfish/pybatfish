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

from pybatfish.datamodel.acl import AclTrace, TextFragment, TraceElement, TraceTree
from pybatfish.datamodel.answer.base import _parse_json_with_schema


# test if an acl trace is deserialized properly
def test_acl_trace_deserialization():
    trace_dict = {"events": [{"description": "aa"}, {"description": "bb"}]}

    # check deserialization
    acl_trace = AclTrace.from_dict(trace_dict)
    assert len(acl_trace.events) == 2

    # check stringification works
    str(acl_trace)


TEXT_FRAGMENT = "org.batfish.datamodel.TraceElement$TextFragment"


def test_trace_tree_no_children():
    trace_tree_dict = {
        "traceElement": {"fragments": [{"class": TEXT_FRAGMENT, "text": "aaa"}]}
    }
    trace_tree = TraceTree.from_dict(trace_tree_dict)
    assert len(trace_tree.children) == 0
    assert str(trace_tree) == "aaa"
    assert trace_tree._repr_html_() == "aaa"


def test_trace_tree_with_children():
    trace_tree_dict = {
        "traceElement": {"fragments": [{"class": TEXT_FRAGMENT, "text": "aaa"}]},
        "children": [
            {"traceElement": {"fragments": [{"class": TEXT_FRAGMENT, "text": "bbb"}]}},
            {"traceElement": {"fragments": [{"class": TEXT_FRAGMENT, "text": "ccc"}]}},
        ],
    }
    trace_tree = TraceTree.from_dict(trace_tree_dict)
    assert len(trace_tree.children) == 2
    assert str(trace_tree) == "\n".join(["aaa", "  - bbb", "  - ccc"])
    html_text = trace_tree._repr_html_()
    assert "aaa" in html_text
    assert "<li>bbb</li>" in html_text
    assert "<li>ccc</li>" in html_text


def test_trace_tree_nested_children():
    trace_tree_dict = {
        "traceElement": {"fragments": [{"class": TEXT_FRAGMENT, "text": "aaa"}]},
        "children": [
            {
                "traceElement": {
                    "fragments": [{"class": TEXT_FRAGMENT, "text": "bbb"}]
                },
                "children": [
                    {
                        "traceElement": {
                            "fragments": [{"class": TEXT_FRAGMENT, "text": "ccc"}]
                        }
                    }
                ],
            },
            {"traceElement": {"fragments": [{"class": TEXT_FRAGMENT, "text": "ddd"}]}},
        ],
    }
    trace_tree = TraceTree.from_dict(trace_tree_dict)
    assert len(trace_tree.children) == 2
    assert len(trace_tree.children[0].children) == 1
    assert str(trace_tree) == "\n".join(["aaa", "  - bbb", "    - ccc", "  - ddd"])
    html_text = trace_tree._repr_html_()
    assert "aaa" in html_text
    assert "<li>bbb <ul>" in html_text
    assert "<ul><li>ccc</li></ul>" in html_text
    assert "<li>ddd</li>" in html_text


def test_trace_tree_list_deserialization():
    raw_trace_tree_list = [
        {"traceElement": {"fragments": [{"class": TEXT_FRAGMENT, "text": "aaa"}]}},
        {"traceElement": {"fragments": [{"class": TEXT_FRAGMENT, "text": "bbb"}]}},
    ]
    trace_tree_list = _parse_json_with_schema("List<TraceTree>", raw_trace_tree_list)
    assert len(trace_tree_list) == 2
    assert trace_tree_list[0] == TraceTree(TraceElement([TextFragment("aaa")]), [])
    assert trace_tree_list[1] == TraceTree(TraceElement([TextFragment("bbb")]), [])


def test_trace_tree_list_representation():
    raw_trace_tree_list = [
        {
            "traceElement": {"fragments": [{"class": TEXT_FRAGMENT, "text": "aaa"}]},
            "children": [
                {
                    "traceElement": {
                        "fragments": [{"class": TEXT_FRAGMENT, "text": "bbb"}]
                    },
                    "children": [
                        {
                            "traceElement": {
                                "fragments": [{"class": TEXT_FRAGMENT, "text": "ccc"}]
                            }
                        }
                    ],
                },
                {
                    "traceElement": {
                        "fragments": [{"class": TEXT_FRAGMENT, "text": "ddd"}]
                    }
                },
            ],
        },
        {
            "traceElement": {"fragments": [{"class": TEXT_FRAGMENT, "text": "eee"}]},
            "children": [
                {
                    "traceElement": {
                        "fragments": [{"class": TEXT_FRAGMENT, "text": "fff"}]
                    }
                }
            ],
        },
    ]
    trace_tree_list = _parse_json_with_schema("List<TraceTree>", raw_trace_tree_list)
    assert str(trace_tree_list) == "\n".join(
        ["- aaa", "  - bbb", "    - ccc", "  - ddd", "- eee", "  - fff"]
    )
    html_text = trace_tree_list._repr_html_().replace(" ", "").replace("\n", "")
    assert html_text == "".join(
        [
            "<ul>",
            "<li>aaa<ul>",
            "<li>bbb<ul>",
            "<li>ccc</li></ul></li>",
            "<li>ddd</li></ul></li>",
            "<li>eee<ul>",
            "<li>fff</li></ul></li>",
            "</ul>",
        ]
    )


if __name__ == "__main__":
    pytest.main()
