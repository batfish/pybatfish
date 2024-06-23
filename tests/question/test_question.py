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
import inspect
import json

import pytest

from pybatfish.client.session import Session
from pybatfish.datamodel import Assertion, AssertionType
from pybatfish.exception import QuestionValidationException
from pybatfish.question.question import (
    _compute_docstring,
    _compute_var_help,
    _has_valid_ordered_variable_names,
    _load_question_dict,
    _load_questions_from_dir,
    _process_variables,
    _validate,
)

TEST_QUESTION_NAME = "testQuestionName"
TEST_QUESTION_DICT = {
    "instance": {
        "instanceName": TEST_QUESTION_NAME,
        "description": "a test question",
        "variables": {
            "var1": {
                "description": "desc1",
                "type": "type1",
                "value": "val1",
                "displayName": "display1",
            }
        },
    }
}


@pytest.fixture()
def session():
    """Session associated with questions created in tests."""
    yield Session(load_questions=False)


def test_min_length():
    numbers = {
        "minElements": 0,
        "minLength": 4,
        "type": "string",
        "value": ["one", "three", "four", "five", "seven"],
    }
    sample_question = {"instance": {"variables": {"numbers": numbers}}}
    expected_message = "\n   Length of value: 'one' for element : 0 of parameter: 'numbers' below minimum length: 4\n"
    with pytest.raises(QuestionValidationException) as err:
        _validate(sample_question)
    assert expected_message == str(err.value)


def test_valid_comparator():
    comparators = {"type": "comparator", "value": ">"}
    sample_question = {"instance": {"comparators": comparators}}
    assert _validate(sample_question)


def test_validate_allowed_values():
    # Test that parameter validates based on "values", not "allowedValues"
    variable = {
        "allowedValues": ["obsolete value"],
        "type": "string",
        "value": "v1",
        "values": [{"name": "v1"}],
    }
    sample_question = {"instance": {"variables": {"v": variable}}}
    assert _validate(sample_question)

    expected_message = (
        "\n   Value: 'obsolete value' is not among allowed"
        + " values ['v1'] of parameter: 'v'\n"
    )
    with pytest.raises(QuestionValidationException) as err:
        variable["value"] = "obsolete value"
        _validate(sample_question)
    assert expected_message == str(err.value)


def test_validate_old_allowed_values():
    # Test that parameter with only "allowedValues" validates based on that
    variable = {"allowedValues": ["v1"], "type": "string", "value": "v1"}
    sample_question = {"instance": {"variables": {"v": variable}}}
    assert _validate(sample_question)

    expected_message = (
        "\n   Value: 'bad value' is not among allowed values "
        + "['v1'] of parameter: 'v'\n"
    )
    with pytest.raises(QuestionValidationException) as err:
        variable["value"] = "bad value"
        _validate(sample_question)
    assert expected_message == str(err.value)


def test_validate_allowed_values_list():
    # Test that list parameter validates based on "values", not "allowedValues"
    variable = {
        "minElements": 0,
        "allowedValues": ["obsolete value"],
        "type": "string",
        "value": ["v1"],
        "values": [{"name": "v1"}],
    }
    sample_question = {"instance": {"variables": {"v": variable}}}
    assert _validate(sample_question)

    expected_message = (
        "\n   Value: 'obsolete value' is not among allowed"
        + " values ['v1'] of parameter: 'v'\n"
    )
    with pytest.raises(QuestionValidationException) as err:
        variable["value"][0] = "obsolete value"
        _validate(sample_question)
    assert expected_message == str(err.value)


def test_validate_old_allowed_values_list():
    # Test that list parameter with only "allowedValues" validates based on that
    variable = {
        "minElements": 0,
        "allowedValues": ["v1"],
        "type": "string",
        "value": ["v1"],
    }
    sample_question = {"instance": {"variables": {"v": variable}}}
    assert _validate(sample_question)

    expected_message = (
        "\n   Value: 'bad value' is not among allowed values "
        + "['v1'] of parameter: 'v'\n"
    )
    with pytest.raises(QuestionValidationException) as err:
        variable["value"][0] = "bad value"
        _validate(sample_question)
    assert expected_message == str(err.value)


def test_compute_docstring():
    assert _compute_docstring("foo", [], {}) == "foo"


def test_compute_var_help_default_value_falsy():
    var_data = {
        "optional": True,
        "description": "Desc",
        "type": "boolean",
        "value": False,
    }
    expected_help = (
        ":param v: Desc\n"
        + "\n"
        + "    Default value: ``False``\n"
        + ":type v: boolean"
    )
    assert _compute_var_help("v", var_data) == expected_help


def test_compute_var_help_with_no_allowed_values():
    var_data = {"optional": True, "description": "Desc", "type": "boolean"}
    expected_help = ":param v: Desc\n" + ":type v: boolean"
    assert _compute_var_help("v", var_data) == expected_help


def test_compute_var_help_with_allowed_values():
    var_data = {
        "optional": True,
        "description": "variable description",
        "values": [
            {"name": "v1", "description": "v1 description"},
            {"name": "v2", "description": "v2 description"},
        ],
        "type": "boolean",
    }
    expected_help = (
        ":param v: variable description"
        + "\n    Allowed values:\n"
        + "\n    * v1: v1 description"
        + "\n    * v2: v2 description"
        + "\n:type v: boolean"
    )
    assert _compute_var_help("v", var_data) == expected_help


def test_compute_var_help_with_new_and_old_allowed_values():
    var_data = {
        "allowedValues": ["deprecated v1"],
        "optional": True,
        "description": "variable description",
        "values": [{"name": "v1", "description": "allowed value description"}],
        "type": "boolean",
    }
    expected_help = (
        ":param v: variable description"
        + "\n    Allowed values:\n"
        + "\n    * v1: allowed value description"
        + "\n:type v: boolean"
    )
    assert _compute_var_help("v", var_data) == expected_help


def test_compute_var_help_with_old_allowed_values():
    var_data = {
        "allowedValues": ["v1"],
        "optional": True,
        "description": "variable description",
        "type": "boolean",
    }
    expected_help = (
        ":param v: variable description"
        + "\n    Allowed values:\n"
        + "\n    * v1"
        + "\n:type v: boolean"
    )
    assert _compute_var_help("v", var_data) == expected_help


def test_process_variables():
    """Test if variable names are returned in the correct order."""
    assert _process_variables("foo", None, None) == []

    variables = {
        "c": {
            "description": "c description",
            "optional": True,
            "type": "boolean",
            "displayName": "c display name",
        },
        "d": {
            "description": "d description",
            "optional": False,
            "type": "boolean",
            "displayName": "d display name",
        },
        "a": {
            "description": "a description",
            "optional": True,
            "type": "boolean",
            "displayName": "a display name",
        },
        "b": {
            "description": "b description",
            "optional": False,
            "type": "boolean",
            "displayName": "b display name",
        },
    }

    # default order: non-optional variables listed alphabetically
    # then optional variables listed alphabetically
    default_variables = ["b", "d", "a", "c"]

    # no ordered_variable_names returns variables in default order
    ordered_variable_names = []
    assert (
        _process_variables("foo", variables, ordered_variable_names)
        == default_variables
    )

    # invalid ordered_variable_names returns variables in default order
    ordered_variable_names = ["d", "c", "b"]
    assert (
        _process_variables("foo", variables, ordered_variable_names)
        == default_variables
    )

    # valid ordered_variable_names returns ordered_variable_names
    ordered_variable_names = ["d", "c", "b", "a"]
    assert (
        _process_variables("foo", variables, ordered_variable_names)
        == ordered_variable_names
    )


def test_has_valid_ordered_variable_names():
    """Test if question has valid orderedVariableNames."""
    variables = {"a": {}, "b": {}, "c": {}}

    # empty ordered_variable_names returns False
    ordered_variable_names = []
    assert not _has_valid_ordered_variable_names(ordered_variable_names, variables)

    # incomplete ordered_variable_names returns False
    ordered_variable_names = ["a"]
    assert not _has_valid_ordered_variable_names(ordered_variable_names, variables)
    ordered_variable_names = ["a", "c"]
    assert not _has_valid_ordered_variable_names(ordered_variable_names, variables)

    # complete ordered_variable_names but with duplicate returns False
    ordered_variable_names = ["a", "c", "b", "b"]
    assert not _has_valid_ordered_variable_names(ordered_variable_names, variables)

    # ordered_variable_names with extraneous variable returns False
    ordered_variable_names = ["a", "c", "b", "d"]
    assert not _has_valid_ordered_variable_names(ordered_variable_names, variables)

    # complete ordered_variable_names return True
    ordered_variable_names = ["a", "c", "b"]
    assert _has_valid_ordered_variable_names(ordered_variable_names, variables)


def test_load_dir_questions(tmpdir, session):
    dir = tmpdir.mkdir("questions")
    dir.join(TEST_QUESTION_NAME + ".json").write(json.dumps(TEST_QUESTION_DICT))
    loaded = _load_questions_from_dir(question_dir=dir.strpath, session=session)
    assert list(loaded.keys()) == [TEST_QUESTION_NAME]

    # test fault tolerance to bad questions
    dir.join("badq.json").write("{")
    loaded = _load_questions_from_dir(question_dir=dir.strpath, session=session)
    assert list(loaded.keys()) == [TEST_QUESTION_NAME]


def test_list_questions(tmpdir):
    dir = tmpdir.mkdir("questions")
    dir.join(TEST_QUESTION_NAME + ".json").write(json.dumps(TEST_QUESTION_DICT))
    bf = Session(load_questions=False)
    bf.q.load(directory=dir.strpath)
    names = [q["name"] for q in bf.q.list()]
    assert names == [TEST_QUESTION_NAME]


def test_make_check(session):
    """Make a check out of the first available question."""
    name, q = _load_question_dict(TEST_QUESTION_DICT, session)
    qdict = q().make_check().dict()
    assert qdict.get("assertion") == Assertion(AssertionType.COUNT_EQUALS, 0).dict()


def test_question_name(session):
    """Test user-set and default question names."""
    qname, qclass = _load_question_dict(TEST_QUESTION_DICT, session)

    has_name = qclass(question_name="manually set")
    assert has_name.get_name() == "manually set"

    inferred_name = qclass()
    assert inferred_name.get_name().startswith("__{}_".format(TEST_QUESTION_NAME))


def test_question_positional_args(session):
    """Test that a question constructor rejects positional arguments."""
    qname, qclass = _load_question_dict(TEST_QUESTION_DICT, session)
    with pytest.raises(TypeError):
        qclass("positional")


def test_question_params(session):
    """Test that a question constructor has right parameters."""
    qname, qclass = _load_question_dict(TEST_QUESTION_DICT, session)
    parameters = inspect.signature(qclass.__init__).parameters

    assert parameters.keys() == {"var1", "question_name"}


if __name__ == "__main__":
    pytest.main()
