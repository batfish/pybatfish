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
"""Tests for issue settings."""

from __future__ import absolute_import, print_function

import pytest

from pybatfish.settings.issues import IssueConfig


def test_issue_config():
    """Check proper deserialization for issue config."""
    dict = {"major": "maj", "minor": "min", "severity": 23, "url": "www.cnn"}
    config = IssueConfig(**dict)

    assert config.major == "maj"
    assert config.minor == "min"
    assert config.severity == 23
    assert config.url == "www.cnn"


def test_issue_config_missing_optional():
    """Check proper deserialization for issue config."""
    dict = {"major": "maj", "minor": "min"}
    IssueConfig.from_dict(dict)  # should not barf


if __name__ == "__main__":
    pytest.main()
