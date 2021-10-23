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

import pytest

from pybatfish.datamodel.acl import (
    Fragment,
    LinkFragment,
    TextFragment,
    TraceElement,
    VendorStructureId,
)

TEXT_FRAGMENT = "org.batfish.datamodel.TraceElement$TextFragment"
LINK_FRAGMENT = "org.batfish.datamodel.TraceElement$LinkFragment"


def test_text_fragment_deserialization():
    fragment_dict = {"class": TEXT_FRAGMENT, "text": "aaa"}
    fragment = Fragment.from_dict(fragment_dict)

    assert isinstance(fragment, TextFragment)
    assert fragment.text == "aaa"


def test_link_fragment_deserialization():
    fragment_dict = {
        "class": LINK_FRAGMENT,
        "text": "aaa",
        "vendorStructureId": {
            "filename": "some-config",
            "structureType": "some-type",
            "structureName": "some-name",
        },
    }
    fragment = Fragment.from_dict(fragment_dict)

    assert isinstance(fragment, LinkFragment)
    assert fragment.text == "aaa"
    assert fragment.vendorStructureId == VendorStructureId(
        "some-config", "some-type", "some-name"
    )


def test_trace_element_deserialization():
    trace_element_dict = {
        "fragments": [
            {"class": TEXT_FRAGMENT, "text": "aaa"},
            {
                "class": LINK_FRAGMENT,
                "text": "bbb",
                "vendorStructureId": {
                    "filename": "aa",
                    "structureType": "bb",
                    "structureName": "cc",
                },
            },
            {"class": TEXT_FRAGMENT, "text": "ccc"},
        ]
    }
    trace_element = TraceElement.from_dict(trace_element_dict)
    assert len(trace_element.fragments) == 3
    assert trace_element.fragments[0] == TextFragment("aaa")
    assert trace_element.fragments[1] == LinkFragment(
        "bbb", VendorStructureId("aa", "bb", "cc")
    )
    assert trace_element.fragments[2] == TextFragment("ccc")


def test_trace_element_str():
    trace_element = TraceElement(
        [
            TextFragment("aaa "),
            LinkFragment("bbb", VendorStructureId("aa", "bb", "cc")),
            TextFragment(" ccc"),
        ]
    )

    assert str(trace_element) == "aaa bbb ccc"


if __name__ == "__main__":
    pytest.main()
