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

import os

import pytest

from pybatfish.exception import QuestionValidationException
from pybatfish.question.question import (_compute_docstring, _compute_var_help,
                                         _process_variables, _validate,
                                         list_questions, load_questions)
from pybatfish.util import validate_json_path_regex


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
        _validate(sample_question)
    assert expected_message == str(err.value)


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
    assert _validate(sample_question)


def test_validate_allowed_values():
    # Test that parameter validates based on "values", not "allowedValues"
    variable = {
        'allowedValues': ['obsolete value'],
        'type': 'string',
        'value': 'v1',
        'values': [{
            'name': 'v1'
        }]
    }
    sample_question = {
        'instance': {
            'variables': {
                'v': variable
            }
        }
    }
    assert _validate(sample_question)

    expected_message = "\n   Value: 'obsolete value' is not among allowed" \
                       + " values ['v1'] of parameter: 'v'\n"
    with pytest.raises(QuestionValidationException) as err:
        variable['value'] = 'obsolete value'
        _validate(sample_question)
    assert expected_message == str(err.value)


def test_validate_old_allowed_values():
    # Test that parameter with only "allowedValues" validates based on that
    variable = {
        'allowedValues': ['v1'],
        'type': 'string',
        'value': 'v1'
    }
    sample_question = {
        'instance': {
            'variables': {
                'v': variable
            }
        }
    }
    assert _validate(sample_question)

    expected_message = "\n   Value: 'bad value' is not among allowed values " \
                       + "['v1'] of parameter: 'v'\n"
    with pytest.raises(QuestionValidationException) as err:
        variable['value'] = 'bad value'
        _validate(sample_question)
    assert expected_message == str(err.value)


def test_validate_allowed_values_list():
    # Test that list parameter validates based on "values", not "allowedValues"
    variable = {
        'minElements': 0,
        'allowedValues': ['obsolete value'],
        'type': 'string',
        'value': ['v1'],
        'values': [{
            'name': 'v1'
        }]
    }
    sample_question = {
        'instance': {
            'variables': {
                'v': variable
            }
        }
    }
    assert _validate(sample_question)

    expected_message = "\n   Value: 'obsolete value' is not among allowed" \
                       + " values ['v1'] of parameter: 'v'\n"
    with pytest.raises(QuestionValidationException) as err:
        variable['value'][0] = 'obsolete value'
        _validate(sample_question)
    assert expected_message == str(err.value)


def test_validate_old_allowed_values_list():
    # Test that list parameter with only "allowedValues" validates based on that
    variable = {
        'minElements': 0,
        'allowedValues': ['v1'],
        'type': 'string',
        'value': ['v1']
    }
    sample_question = {
        'instance': {
            'variables': {
                'v': variable
            }
        }
    }
    assert _validate(sample_question)

    expected_message = "\n   Value: 'bad value' is not among allowed values " \
                       + "['v1'] of parameter: 'v'\n"
    with pytest.raises(QuestionValidationException) as err:
        variable['value'][0] = 'bad value'
        _validate(sample_question)
    assert expected_message == str(err.value)


def test_compute_docstring():
    assert _compute_docstring("foo", [], {}) == "foo"


def test_compute_var_help_with_no_allowed_values():
    var_data = {
        "optional": True,
        "description": "Desc",
        "type": "boolean"
    }
    expected_help = ":param v: Desc\n" \
                    + ":type v: boolean"
    assert _compute_var_help("v", var_data) == expected_help


def test_compute_var_help_with_allowed_values():
    var_data = {
        "optional": True,
        "description": "variable description",
        "values": [
            {"name": "v1", "description": "v1 description"},
            {"name": "v2", "description": "v2 description"}
        ],
        "type": "boolean"
    }
    expected_help = ":param v: variable description" \
                    + "\n    Allowed values:"\
                    + "\n      * v1: v1 description" \
                    + "\n      * v2: v2 description" \
                    + "\n:type v: boolean"
    assert _compute_var_help("v", var_data) == expected_help


def test_compute_var_help_with_new_and_old_allowed_values():
    var_data = {
        "allowedValues": ["deprecated v1"],
        "optional": True,
        "description": "variable description",
        "values": [{"name": "v1", "description": "allowed value description"}],
        "type": "boolean"
    }
    expected_help = ":param v: variable description" \
                    + "\n    Allowed values:"\
                    + "\n      * v1: allowed value description" \
                    + "\n:type v: boolean"
    assert _compute_var_help("v", var_data) == expected_help


def test_compute_var_help_with_old_allowed_values():
    var_data = {
        "allowedValues": ["v1"],
        "optional": True,
        "description": "variable description",
        "type": "boolean"
    }
    expected_help = ":param v: variable description" \
                    + "\n    Allowed values:"\
                    + "\n      * v1" \
                    + "\n:type v: boolean"
    assert _compute_var_help("v", var_data) == expected_help


def test_process_variables():
    assert _process_variables("foo", None) == []


def test_list_questions():
    current_path = os.path.abspath(os.path.dirname(__file__))
    question_directory = os.path.join(current_path, "../../questions")
    load_questions(question_dir=question_directory)
    assert list_questions() != []
