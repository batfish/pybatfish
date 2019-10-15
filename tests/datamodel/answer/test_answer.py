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
"""Tests for Answer class."""

from __future__ import absolute_import, print_function

import pytest

from pybatfish.datamodel.answer import Answer


def test_blank_question_name():
    """Answer sets question name to None if there is no question name."""
    answer = Answer({})
    assert answer.question_name() is None
    dictionary = {"question": {}}
    answer = Answer(dictionary)
    assert answer.question_name() is None
    dictionary = {"question": {"instance": {}}}
    answer = Answer(dictionary)
    assert answer.question_name() is None


def test_question_name():
    """Answer provides correct question name."""
    dictionary = {
        "answerElements": [],
        "question": {"instance": {"instanceName": "q_name"}},
    }
    answer = Answer(dictionary)
    assert answer.question_name() == "q_name"


if __name__ == "__main__":
    pytest.main()
