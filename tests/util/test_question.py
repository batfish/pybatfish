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

from pybatfish.exception import QuestionValidationException
from pybatfish.question import question
from pybatfish.question.question import _compute_docstring, _process_variables
from pybatfish.util import validate_json_path_regex
import pytest


def test_validate_json_path_regex():
    assert validate_json_path_regex("/x/")
    assert validate_json_path_regex("/x/i")
    assert validate_json_path_regex("/\w+\d.*/i")
    with pytest.raises(QuestionValidationException):
        assert validate_json_path_regex("foo")
    with pytest.raises(QuestionValidationException):
        assert validate_json_path_regex("/foo")


def test_min_length():
    numbers = {
        'minElements': 0,
        'minLength': 4,
        'type': 'string',
        'value': ['one', 'three', 'four', 'five', 'seven']
    }
    sample_question = {
        'instance': {
            'variables': {
                'numbers': numbers
            }
        }
    }
    expected_message = "\n   Length of value: 'one' for element : 0 of parameter: 'numbers' below minimum length: 4\n"
    with pytest.raises(QuestionValidationException) as err:
        question._validate(sample_question)
        assert expected_message in err


def test_valid_comparator():
    comparators = {
        'type': 'comparator',
        'value': '>'
    }
    sample_question = {
        'instance': {
            'comparators': comparators
        }
    }
    assert question._validate(sample_question)


def test_compute_docstring():
    assert _compute_docstring("foo", None) == "foo"


def test_process_variables():
    assert _process_variables("foo", None) == []
