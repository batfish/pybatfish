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
"""Tests for reference library."""

from __future__ import absolute_import, print_function

import pytest

from pybatfish.datamodel.referencelibrary import ReferenceLibrary


def test_empty_referencelibrary():
    """Check proper deserialization for a reference library dict."""
    dict = {}
    reference_library = ReferenceLibrary(**dict)
    assert len(reference_library.books) == 0

    dict = {
        "books": []
    }
    reference_library = ReferenceLibrary(**dict)
    assert len(reference_library.books) == 0


def test_non_empty_referencelibrary():
    """Check proper deserialization for a reference library dict."""
    dict = {
        "books": [
            {
                "name": "book1",
                "addressGroups": [
                    {
                        "name": "ag1",
                        "addresses": [
                            "1.1.1.1/24",
                            "2.2.2.2",
                            "3.3.3.3:0.0.0.8"
                        ]
                    },
                    {
                        "name": "ag2"
                    }
                ]
            },
            {
                "name": "book2",
            }
        ]
    }
    reference_library = ReferenceLibrary(**dict)

    assert len(reference_library.books) == 2
    assert reference_library.books[0].name == "book1"
    assert len(reference_library.books[0].addressGroups) == 2
    assert reference_library.books[0].addressGroups[0].name == "ag1"
    assert len(reference_library.books[0].addressGroups[0].addresses) == 3


if __name__ == "__main__":
    pytest.main()
