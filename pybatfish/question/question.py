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
"""Defines Batfish questions and logic for loading them from disk or Batfish."""

from __future__ import absolute_import, print_function

import json
import logging
import os
import re
import sys
from copy import deepcopy
from inspect import getmembers
from typing import (Any, Dict, Iterable, List, Optional, Set,  # noqa: F401
                    Tuple, Union)

import attr
import six
from six import PY3, integer_types, string_types

from pybatfish.client.internal import (_bf_answer_obj,
                                       _bf_get_question_templates)
from pybatfish.datamodel import Assertion, AssertionType, \
    VariableType  # noqa: F401
from pybatfish.datamodel.answer import Answer  # noqa: F401
from pybatfish.exception import QuestionValidationException
from pybatfish.question import bfq
from pybatfish.util import BfJsonEncoder, get_uuid, validate_question_name

# A set of tags across all questions
_tags = set()  # type: Set[str]
_VALID_VARIABLE_NAME_REGEX = re.compile(r'^\w+$')

__all__ = [
    'list_questions',
    'list_tags',
    'load_dir_questions',
    'load_questions',
]

bf_logger = logging.getLogger("pybatfish.client")


@attr.s(frozen=True)
class AllowedValue(object):
    """Describes a whitelisted value for a question parameter."""

    name = attr.ib(type=str)
    description = attr.ib(type=Optional[str], default=None)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> AllowedValue
        return AllowedValue(json_dict['name'], json_dict.get('description'))

    def __str__(self):
        if self.description is not None:
            return "{}: {}".format(self.name, self.description)
        return self.name


class QuestionMeta(type):
    """A meta class for all Question classes."""

    def __new__(cls, name, base, dct):
        """Creates a new class for a specific question."""
        new_cls = super(QuestionMeta, cls).__new__(cls, name, base, dct)
        additional_kwargs = {'question_name'}

        def constructor(self, *args, **kwargs):
            """Create a new question."""
            # Reject positional args; this way is PY2-compliant
            if args:
                raise TypeError("Please use keyword arguments")

            # Call super (i.e., QuestionBase)
            super(new_cls, self).__init__(new_cls.template)

            # Update well-known params, if passed in
            if "exclusions" in kwargs:
                self._dict['exclusions'] = kwargs.get("exclusions")
            if "question_name" in kwargs:
                self._dict['instance']['instanceName'] = kwargs.get(
                    "question_name")
            else:
                self._dict['instance']['instanceName'] = (
                    "__{}_{}".format(
                        self._dict['instance']['instanceName'], get_uuid()))

            # Validate that we are not accepting invalid kwargs/variables
            instance_vars = self._dict['instance'].get('variables', {})
            allowed_kwargs = set(instance_vars)
            allowed_kwargs.update(additional_kwargs)
            var_difference = set(kwargs.keys()).difference(allowed_kwargs)
            if var_difference:
                raise QuestionValidationException(
                    "Received unsupported parameters/variables: {}".format(
                        var_difference))
            # Set question-specific parameters
            for var_name, var_value in kwargs.items():
                if var_name not in additional_kwargs:
                    instance_vars[var_name]['value'] = var_value

        # Define signature. Helps with tab completion. Python3 centric
        if PY3:
            from inspect import Signature, Parameter
            # Merge constructor params with question variables
            params = [Parameter(name=param, kind=Parameter.KEYWORD_ONLY)
                      for param in dct.get("variables", []) +
                      [p for p in additional_kwargs if
                       p not in ('kwargs', 'self')]]
            setattr(constructor, '__signature__', Signature(parameters=params))
        setattr(new_cls, '__init__', constructor)
        setattr(new_cls, '__doc__', dct.get("docstring", ""))
        new_cls.description = dct.get("description", "")
        new_cls.tags = dct.get("tags", [])
        new_cls.template = dct.get('template', {})

        return new_cls

    def __dir__(self):
        return ['description', 'tags', 'template'] + list(
            reversed(dir(QuestionBase)))


class QuestionBase(object):
    """All questions inherit functionality from this class."""

    def __init__(self, dictionary):
        self._dict = deepcopy(dictionary)

    def answer(self, snapshot=None, reference_snapshot=None,
               include_one_table_keys=None, background=False, extra_args=None):
        # type: (Optional[str], Optional[str], Optional[bool], bool, Optional[Dict[str, Any]]) -> Union[str, Answer]
        """
        Ask and return the answer for this question.

        :param snapshot: the snapshot on which to answer the question. If not
            provided, the latest snapshot initialized will be used.
        :type snapshot: str
        :param reference_snapshot: for differential questions only, the snapshot
            against which to compare.
        :type reference_snapshot: str
        :param include_one_table_keys: if differential is True, include keys only
            from one table and not both.
        :type include_one_table_keys: bool
        :param background: run this question in background, return immediately
        :type background: bool
        :param extra_args: extra arguments to be passed to the parse command. See bf_session.additionalArgs.
        :type extra_args: dict
        :rtype: :py:class:`~pybatfish.datamodel.answer.base.Answer` or
            :py:class:`~pybatfish.datamodel.answer.table.TableAnswer`

        :raises QuestionValidationException: if the question is malformed
        """
        from pybatfish.client.commands import bf_session
        real_snapshot = bf_session.get_snapshot(snapshot)
        if reference_snapshot is None and self.get_differential():
            raise ValueError(
                "reference_snapshot argument is required to answer a differential question")
        _validate(self.dict())
        if include_one_table_keys is not None:
            self._set_include_one_table_keys(include_one_table_keys)
        return _bf_answer_obj(self.json(),
                              parameters_str="{}",
                              question_name=self.get_name(),
                              background=background,
                              snapshot=real_snapshot,
                              reference_snapshot=reference_snapshot,
                              extra_args=extra_args)

    def dict(self):
        """Return the dictionary representing this question."""
        return self._dict

    def json(self, **kwargs):
        """Return the json string representing this question.

        Keyword arguments passed to json.dumps with default assignments of
        sort_keys=True and indent=2

        .. deprecated: 0.36.0
        """
        return json.dumps(self._dict, sort_keys=True, indent=2,
                          cls=BfJsonEncoder, **kwargs)

    def get_description(self):
        """Return the short description of this question."""
        return self._dict['instance']['description']

    def get_long_description(self):
        """Return the long description of this question."""
        return self._dict['instance']['longDescription']

    def get_differential(self):
        """Return whether this question is to be asked differentially."""
        return self._dict.get('differential', False)

    def get_include_one_table_keys(self):
        """Return whether keys present in only one table should be included when computing answer table diffs."""
        return self._dict.get('includeOneTableKeys', False)

    def get_name(self):
        """Return the name of this question."""
        return self._dict['instance']['instanceName']

    def _set_include_one_table_keys(self, include_one_table_keys):
        """Set if keys present in only table should be included when computing table diffs."""
        self._dict['includeOneTableKeys'] = include_one_table_keys

    def set_assertion(self, assertion):
        # type: (Assertion) -> QuestionBase
        """Set an assertion for a given question.

        Overwrites any previous assertions.
        """
        self._dict['assertion'] = assertion.dict()
        return self

    def make_check(self):
        # type: () -> QuestionBase
        """Make this question a check which asserts that there are no results."""
        self.set_assertion(Assertion(AssertionType.COUNT_EQUALS, 0))
        return self


def list_questions(tags=None, question_module='pybatfish.question.bfq'):
    # type: (Optional[Iterable[str]], str) -> List[Dict[str, Union[str, Set]]]
    """List available questions.

    :param tags: if not `None`, only list questions with given tags.
        See :py:func:`list_tags` for a list of tags given currently loaded questions.
    :param question_module: which module to load the questions from. By default,
        :py:mod:`pybatfish.question.bfq` is used.

    :returns: a list of questions, where each question is represented as a dict
        containing "name", "description", and "tags".
    """
    module = sys.modules[question_module]
    # Members of the module are (name,value) pairs so
    # x[1] in the lambda represents the value part.
    # Want members with value of type QuestionMeta
    predicate = lambda x: isinstance(x[1], QuestionMeta)
    question_functions = filter(predicate, getmembers(module))

    matching_questions = []
    desired_tags = set(
        map(str.lower, tags)) if tags else set()  # type: Set[str]
    for name, question_func in question_functions:
        if desired_tags and not desired_tags.intersection(
                map(str.lower, question_func.tags)):
            # skip questions that don't have any desired tags
            continue

        matching_questions.append({
            'name': name,
            'description': question_func.description,
            'tags': question_func.tags,
        })
    return matching_questions


def list_tags():
    # type: () -> Set[str]
    """List tags across all available questions."""
    return _tags


def _install_questions_in_module(questions, module_name):
    # type: (Iterable[Tuple[str, QuestionMeta]], str) -> None
    """Install the given questions in the specified module."""
    module = sys.modules[module_name]
    for (name, question_class) in questions:
        setattr(question_class, '__module__', module_name)
        setattr(module, name, question_class)


def _load_questions_from_dir(question_dir):
    # type: (str) -> Dict[str, QuestionMeta]
    question_files = []
    for dirpath, dirnames, filenames in os.walk(question_dir):
        for filename in filenames:
            if filename.endswith(".json"):
                question_files.append(os.path.join(dirpath, filename))
    if len(question_files) == 0:
        bf_logger.warn(
            "WARNING: no .json files found in supplied question directory: {questionDir}".format(
                questionDir=question_dir))
        return {}

    questions = {}
    for questionFile in question_files:
        try:
            (qname, qclass) = _load_question_disk(questionFile)
            questions[qname] = qclass
        except Exception as err:
            bf_logger.error(
                "Could not load question from {questionFile}:{err}".format(
                    questionFile=questionFile,
                    err=err))
    bf_logger.info(
        "Successfully loaded {numQuestions}/{numQuestionFiles} question(s) from local directory".format(
            numQuestions=len(questions), numQuestionFiles=len(question_files)))
    return questions


def load_dir_questions(questionDir, moduleName=bfq.__name__):
    # type: (str, str) -> Iterable[str]
    """Load question templates from a directory on disk and install them in the given module."""
    # Find all files with questions in them.
    questions = _load_questions_from_dir(questionDir)
    _install_questions_in_module(six.iteritems(questions), moduleName)
    return questions.keys()


def _load_question_disk(question_path):
    # type: (str) -> Tuple[str, QuestionMeta]
    """Load a question template from disk and instantiate a new `:py:class:Question`."""
    with open(question_path, 'r') as question_file:
        question_dict = json.load(question_file)
    try:
        return _load_question_dict(question_dict)
    except QuestionValidationException as e:
        raise QuestionValidationException(
            "Error loading question from {}".format(question_path), e)


def _load_question_dict(question):
    # type: (Dict[str, Any]) -> Tuple[str, QuestionMeta]
    """Create a question from a dictionary which contains a template.

    :return the name of the question
    """
    # Perform series of validations on the question.
    # Try to have meaningful error messages.

    # Check has instance data
    instance_data = question.get('instance')
    if not instance_data:
        raise QuestionValidationException("Missing instance data")

    # name validation
    given_question_name = instance_data.get('instanceName')
    if not given_question_name or not validate_question_name(
            given_question_name):
        raise QuestionValidationException(
            "Invalid question name: {}".format(given_question_name))
    question_name = str(given_question_name)  # type: str

    # description validation
    question_description = instance_data.get(
        'description', '').strip()  # type: str
    if not question_description:
        raise QuestionValidationException(
            "Missing description for question '{}'".format(question_name))
    if not question_description.endswith('.'):
        question_description += '.'

    # Extend description if we can
    long_description = instance_data.get(
        'longDescription', '').strip()  # type: str
    if long_description:
        if not long_description.endswith('.'):
            long_description += '.'
        question_description = "\n\n".join(
            [question_description, long_description])

    # Extract question tags
    tags = sorted(map(str, instance_data.get('tags', [])))
    _tags.update(tags)

    # Validate question variables
    ivars = instance_data.get('variables', {})
    ordered_variable_names = instance_data.get('orderedVariableNames', [])
    variables = _process_variables(question_name, ivars, ordered_variable_names)

    # Compute docstring
    docstring = _compute_docstring(question_description, variables, ivars)

    # Make new Question class
    question_class = QuestionMeta(question_name, (QuestionBase,), {
        'docstring': docstring,
        'description': question_description,
        'tags': tags,
        'template': deepcopy(question),
        'variables': variables,
    })
    return question_name, question_class


def _process_variables(question_name, variables, ordered_variable_names):
    # type: (str, Dict[str, Dict[str, Any]], List[str]) -> List[str]
    """Perform validation on question variables.

    :returns an ordered list of variable names
    """
    if not variables:
        return []
    for var_name, var_data in variables.items():
        _validate_variable_name(question_name, var_name)
        _validate_variable_data(question_name, var_name, var_data)

    if _has_valid_ordered_variable_names(ordered_variable_names, variables):
        return ordered_variable_names

    def __var_key(name):
        """Orders required [!optional] vars first, then by name."""
        return variables[name].get('optional', False), name

    return sorted(variables.keys(), key=__var_key)


def _validate_variable_data(question_name, var_name, var_data):
    # type: (str, str, Dict[str, Any]) -> bool
    """Perform validation on variable metadata and fix style if necessary.

    :raises QuestionValidationException if metadata is invalid.
    """
    var_type = var_data.get('type', '').strip()
    if not var_type:
        raise QuestionValidationException(
            "Question {} is missing type for variable {}".format(
                question_name,
                var_name))
    var_data['type'] = var_type

    var_desc = var_data.get('description', '').strip()
    if not var_desc:
        raise QuestionValidationException(
            "Question {} is missing description for variable {}".format(
                question_name,
                var_name))
    if not var_desc.endswith('.'):
        var_desc += '.'
    var_data['description'] = var_desc

    return True


def _validate_variable_name(question_name, var_name):
    # type: (str, str) -> bool
    """Check if the variable name is valid."""
    if not re.match(_VALID_VARIABLE_NAME_REGEX, var_name):
        raise QuestionValidationException(
            "Question {} has invalid variable name: {}. Only alphanumeric characters are allowed".format(
                question_name, var_name))
    return True


def _has_valid_ordered_variable_names(ordered_variable_names, variables):
    # type: (List[str], Dict[str, Dict[str, Any]]) -> bool
    """Check if orderedVariableNames is present and that it includes all instance variables."""
    if not ordered_variable_names:
        return False
    set_of_ordered_variable_names = frozenset(ordered_variable_names)
    set_of_variable_names = frozenset(variables.keys())
    has_unique_ordered_variable_names = len(set_of_ordered_variable_names) == len(ordered_variable_names)
    has_all_variable_names = set_of_ordered_variable_names == set_of_variable_names
    return has_unique_ordered_variable_names and has_all_variable_names


def _compute_docstring(base_docstring, var_names, variables):
    # type: (str, List[str], Dict[str, Any]) -> str
    """Compute a docstring for a question, based on the variables."""
    if not variables:
        return base_docstring
    return "\n".join([base_docstring, "\n"] +
                     [_compute_var_help(var, variables[var]) for var in
                      var_names])


def _compute_var_help(var_name, var_data):
    # type: (str, Dict[str, Any]) -> str
    """Create explanation of a single question variable."""
    # Variable help has 2 sections: param and type. Param section may include
    # optionally: required (inline), and allowed_values and/or default_value on
    # their own lines with a leading blank.
    param_line = ":param {name}: {opt_req}{desc}\n".format(
        name=var_name,
        opt_req='*Required.* ' if not var_data.get('optional',
                                                   False) else "",
        desc=var_data['description'])

    allowed_values = _build_allowed_values(var_data)
    if allowed_values:
        param_line += "    Allowed values:\n\n    * {}\n".format(
            '\n    * '.join([str(v) for v in allowed_values]))

    default_value = var_data.get("value", "")
    if default_value:
        param_line += "\n    Default value: ``{}``\n".format(default_value)

    type_line = ":type {name}: {type}".format(
        name=var_name, type=var_data["type"])

    return param_line + type_line


def _build_allowed_values(var_data):
    values_dict = var_data.get('values')
    if values_dict:
        return [AllowedValue.from_dict(v) for v in values_dict]
    old_values_dict = var_data.get('allowedValues')
    if old_values_dict:
        return [AllowedValue(v) for v in old_values_dict]
    return None


def load_questions(question_dir=None, from_server=False,
                   module_name=bfq.__name__):
    # type: (Optional[str], bool, str) -> None
    """Load questions from directory or batfish service.

    :param question_dir: Load questions from this local directory instead of
        remote questions from the batfish service.
    :type question_dir: str
    :param from_server: if true or `question_dir` is None, load questions from
        service.
    :type from_server: bool
    :param module_name: the name of the module where questions should be loaded.
        Default is :py:mod:`pybatfish.question.bfq`
    """
    new_names = set()  # type: Set[str]
    if not question_dir or from_server:
        remote_questions = _load_remote_questions_templates()
        _install_questions_in_module(remote_questions, module_name)
        new_names |= set(name for name, q in remote_questions)
    if question_dir:
        local_questions = load_dir_questions(question_dir,
                                             moduleName=module_name)
        over_written_questions = len(set(local_questions) & new_names)
        if over_written_questions > 0:
            bf_logger.info(
                "Overwrote {over_written_questions} remote question(s) with local question(s)".format(
                    over_written_questions=over_written_questions))


def _load_remote_questions_templates():
    # type: () -> Set[Tuple[str, QuestionMeta]]
    num_questions = 0
    remote_questions = set()
    questions_dict = _bf_get_question_templates()
    for (key, value) in questions_dict.items():
        try:
            remote_questions.add(_load_question_dict(json.loads(value)))
            num_questions += 1
        except Exception as err:
            bf_logger.error(
                "Could not load question {name} : {err}".format(name=key,
                                                                err=err))
    bf_logger.info(
        "Successfully loaded {numQuestions} questions from remote".format(
            numQuestions=num_questions))
    return remote_questions


def _validate(questionJson):
    valid = True
    errorMessage = '\n'
    instanceData = questionJson['instance']
    if 'variables' in instanceData:
        variables = instanceData['variables']
        for variableName, variable in variables.items():
            # First check for missing mandatory parameters
            optional = False
            if 'optional' in variable:
                optional = variable['optional']
            if not optional:
                if 'value' not in variable:
                    valid = False
                    errorMessage += "   Missing value for mandatory parameter: '" + variableName + "'\n"

            # Now do some dynamic type-checking
            allowed_values = _build_allowed_values(variable)
            if 'value' in variable:
                value = variable['value']
                variableType = variable['type']
                minLength = None
                if 'minLength' in variable:
                    minLength = variable['minLength']
                isArray = 'minElements' in variable
                if isArray:
                    if not isinstance(value, list):
                        valid = False
                        errorMessage += "   Expected a list for parameter: '" + variableName + "'\n"
                    else:
                        minElements = variable['minElements']
                        if len(value) < minElements:
                            valid = False
                            errorMessage += "   Number of elements provided for parameter: '" + variableName + "' less than the minimum: " + str(
                                minElements) + "\n"
                        else:
                            for i in range(0, len(value)):
                                valueElement = value[i]
                                typeValid = _validateType(valueElement,
                                                          variableType)
                                if not typeValid:
                                    valid = False
                                    errorMessage += "   Expected type: '" + variableType + "' for element: " + str(
                                        i) + " of parameter: "' + variableName + '"\n"
                                elif minLength and len(
                                        valueElement) < minLength:
                                    valid = False
                                    errorMessage += "   Length of value: '" + valueElement + "' for element : " + str(
                                        i) + " of parameter: '" + variableName + "' below minimum length: " + str(
                                        minLength) + "\n"
                                elif allowed_values is not None and valueElement not in \
                                        [v.name for v in allowed_values]:
                                    valid = False
                                    errorMessage += "   Value: '{}' is not among allowed values {} of parameter: '{}'\n".format(
                                        valueElement,
                                        [v.name for v in allowed_values],
                                        variableName)

                else:
                    typeValid, typeValidErrorMessage = _validateType(value,
                                                                     variableType)
                    if not typeValid:
                        valid = False
                        if typeValidErrorMessage:
                            errorMessage += "   Expected type: '" + variableType + "' for parameter: '" + variableName + "'. Got error: '" + typeValidErrorMessage + "'\n"
                        else:
                            errorMessage += "   Expected type: '" + variableType + "' for parameter: '" + variableName + "'\n"
                    elif minLength and len(value) < minLength:
                        valid = False
                        errorMessage += "   Length of value: '" + value + "' for parameter: '" + variableName + "' below minimum length: " + str(
                            minLength) + "\n"
                    elif allowed_values is not None and value not in \
                            [v.name for v in allowed_values]:
                        valid = False
                        errorMessage += "   Value: '{}' is not among allowed values {} of parameter: '{}'\n".format(
                            value, [v.name for v in allowed_values],
                            variableName)
    if not valid:
        raise QuestionValidationException(errorMessage)
    return True


def _validateType(value, expectedType):
    """
    Check if the input `value` have contents that matches the requirements specified by `expectedType`.

    Return a tuple, first element in the tuple is a boolean tells the validation result, while
    the second element contains the error message if there is one.

    :raises QuestionValidationException
    """
    if expectedType == VariableType.BOOLEAN:
        return isinstance(value, bool), None
    elif expectedType == VariableType.COMPARATOR:
        validComparators = ['<', '<=', '==', '>=', '>', '!=']
        if value not in validComparators:
            return False, "'{}' is not a known comparator. Valid options are: '{}'".format(
                value,
                ", ".join(validComparators))
        return True, None
    elif expectedType == VariableType.INTEGER:
        INT32_MIN = -2 ** 32
        INT32_MAX = 2 ** 32 - 1
        valid = (isinstance(value, integer_types) and
                 INT32_MIN <= value <= INT32_MAX)
        return valid, None
    elif expectedType == VariableType.FLOAT:
        return isinstance(value, float), None
    elif expectedType == VariableType.DOUBLE:
        return isinstance(value, float), None
    elif expectedType in [
        VariableType.ADDRESS_BOOK,
        VariableType.ADDRESS_GROUP,
        VariableType.BGP_PEER_PROPERTY_SPEC,
        VariableType.BGP_PROCESS_PROPERTY_SPEC,
        VariableType.BGP_SESSION_STATUS,
        VariableType.BGP_SESSION_TYPE,
        VariableType.DISPOSITION_SPEC,
        VariableType.FILTER,
        VariableType.FLOW_STATE,
        VariableType.INTEGER_SPACE,
        VariableType.INTERFACE,
        VariableType.INTERFACE_PROPERTY_SPEC,
        VariableType.INTERFACES_SPEC,
        VariableType.IPSEC_SESSION_STATUS,
        VariableType.JAVA_REGEX,
        VariableType.JSON_PATH_REGEX,
        VariableType.NAMED_STRUCTURE_SPEC,
        VariableType.NODE_PROPERTY_SPEC,
        VariableType.NODE_ROLE_DIMENSION,
        VariableType.NODE_SPEC,
        VariableType.OSPF_PROPERTY_SPEC,
        VariableType.ROUTING_PROTOCOL_SPEC,
        VariableType.STRUCTURE_NAME,
        VariableType.VRF,
        VariableType.VXLAN_VNI_PROPERTY_SPEC,
        VariableType.ZONE,
    ]:
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        return True, None
    elif expectedType == VariableType.IP:
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        else:
            return _isIp(value)
    elif expectedType == VariableType.IP_WILDCARD:
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        else:
            return _isIpWildcard(value)
    elif expectedType == VariableType.JSON_PATH:
        return _isJsonPath(value)
    elif expectedType == VariableType.LONG:
        INT64_MIN = -2 ** 64
        INT64_MAX = 2 ** 64 - 1
        valid = (isinstance(value, integer_types) and
                 INT64_MIN <= value <= INT64_MAX)
        return valid, None
    elif expectedType == VariableType.PREFIX:
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        else:
            return _isPrefix(value)
    elif expectedType == VariableType.PREFIX_RANGE:
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        else:
            return _isPrefixRange(value)
    elif expectedType == VariableType.QUESTION:
        return isinstance(value, QuestionBase), None
    elif expectedType == VariableType.STRING:
        return isinstance(value, string_types), None
    elif expectedType == VariableType.SUBRANGE:
        if isinstance(value, int):
            return True, None
        elif isinstance(value, string_types):
            return _isSubRange(value)
        else:
            return False, "A Batfish {} must either be a string or an integer".format(
                expectedType)
    elif expectedType == VariableType.PROTOCOL:
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        else:
            validProtocols = ['dns', 'ssh', 'tcp', 'udp']
            if not value.lower() in validProtocols:
                return False, "'{}' is not a valid protocols. Valid options are: '{}'".format(
                    value,
                    ", ".join(validProtocols))
            return True, None
    elif expectedType == VariableType.IP_PROTOCOL:
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        else:
            try:
                intValue = int(value)
                if not 0 <= intValue < 256:
                    return False, "'{}' is not in valid ipProtocol range: 0-255".format(
                        intValue)
                return True, None
            except ValueError:
                # TODO: Should be validated at server side
                return True, None
    elif expectedType in [
        VariableType.ANSWER_ELEMENT,
        VariableType.HEADER_CONSTRAINT,
        VariableType.PATH_CONSTRAINT,
    ]:
        return True, None
    else:
        bf_logger.warn(
            "WARNING: skipping validation for unknown argument type {}".format(
                expectedType))
        return True, None


def _isJsonPath(value):
    """
    Check if the input string represents a valid jsonPath.

    Return a tuple, first element in the tuple is a boolean tells the validation result, while
    the second element contains the error message if there is one.
    """
    if not isinstance(value, dict):
        return False, "Expected a jsonPath dictionary with elements 'path' (string) and optional 'suffix' (boolean)"
    elif 'path' not in value:
        return False, "Missing 'path' element of jsonPath"
    else:
        path = value['path']
        if not isinstance(path, string_types):
            return False, "'path' element of jsonPath dictionary should be a string"
        if 'suffix' in value:
            suffix = value['suffix']
            if not isinstance(suffix, bool):
                return False, "'suffix' element of jsonPath dictionary should be a boolean"
        return True, None


def _isIp(value):
    """
    Check if the input string represents a valid IP address.

    A valid IP can be one of the two forms:

    1. A string that contains three '.' which separate the string into
    four segments, each segment is an integer.

    2. A string be either "INVALID_IP(XXXl)" or "AUTO/NONE(XXXl)",
    where XXX is a long value.

    Return a tuple, first element in the tuple is a boolean tells the validation result, while
    the second element contains the error message if there is one.
    """
    addrArray = value.split('.')
    if not len(addrArray) == 4:
        if value.startswith('INVALID_IP') or value.startswith('AUTO/NONE'):
            tail = value.split('(')
            if len(tail) == 2:
                longStrParts = tail[1].split("l")
                if len(longStrParts) == 2:
                    try:
                        int(longStrParts[0])
                        return True, None
                    except ValueError:
                        return False, "Invalid ip string: '{}'".format(
                            value)
        return False, "Invalid ip string: '{}'".format(value)
    else:
        for segments in addrArray:
            try:
                segmentVal = int(segments)
            except ValueError:
                return False, "Ip segment is not a number: '{}' in ip string: '{}'".format(
                    segments, value)
            if not 0 <= segmentVal <= 255:
                return False, "Ip segment is out of range 0-255: '{}' in ip string: '{}'".format(
                    segments, value)
        return True, None


def _isSubRange(value):
    """
    Check if the input string represents a valid subRange.

    Return a tuple, first element in the tuple is a boolean tells the validation result, while
    the second element contains the error message if there is one.
    """
    contents = value.split("-")
    if len(contents) != 2:
        return False, "Invalid subRange: {}".format(value)
    try:
        int(contents[0])
    except ValueError:
        return False, "Invalid subRange start: {}".format(contents[0])
    try:
        int(contents[1])
    except ValueError:
        return False, "Invalid subRange end: {}".format(contents[1])
    return True, None


def _isPrefix(value):
    """
    Check if the input string represents a valid prefix.

    A prefix contains two parts separated by '/'. The first part represents a
    valid IP address, the second part is an integer value.

    Return a tuple, first element in the tuple is a boolean tells the validation
    result, while the second element contains the error message if there is one.
    """
    contents = value.split("/")
    if not len(contents) == 2:
        return False, "Invalid prefix string: '{}'".format(value)
    try:
        int(contents[1])
    except ValueError:
        return False, "Prefix length must be an integer"
    return _isIp(contents[0])


def _isPrefixRange(value):
    """
    Check if the input string represents a valid prefix range.

    A prefix range contains a valid prefix, a ":", then an optional subrange.

    Return a tuple, first element in the tuple is a boolean tells the validation
    result, while the second element contains the error message if there is one.
    """
    contents = value.split(":")
    if len(contents) < 1 or len(contents) > 2:
        return False, "Invalid PrefixRange string: '{}'".format(value)
    if not _isPrefix(contents[0])[0]:
        return False, "Invalid prefix string: '{}' in prefix range string: '{}'".format(
            contents[0], value)
    if len(contents) == 2:
        return _isSubRange(contents[1])
    return True, None


def _isIpWildcard(value):
    """
    Check if the input string represents a valid ipWildCard.

    A valid ipWildcard can be one of the three forms:

    1. A normal IP address (_isIp() returns true)

    2. A string contains a ':', each side of the colon is a valid IP address

    3. A string contains a '/', left side of the slash is a valid IP address,
       the right side of the slash is an integer

    Return a tuple, first element in the tuple is a boolean tells the validation
    result, while the second element contains the error message if there is one.
    """
    if ":" in value:
        contents = value.split(":")
        if not len(contents) == 2:
            return False, "Invalid IpWildcard string: '{}'".format(value)
        if not _isIp(contents[0])[0]:
            return False, "Invalid ip string: '{}'".format(contents[0])
        else:
            return _isIp(contents[1])
    elif "/" in value:
        contents = value.split("/")
        if not len(contents) == 2:
            return False, "Invalid IpWildcard string: '{}'".format(value)
        if not _isIp(contents[0])[0]:
            return False, "Invalid ip string: '{}'".format(contents[0])
        else:
            try:
                int(contents[1])
                return True, None
            except ValueError:
                return False, "Invalid prefix length: '{}' in IpWildcard string: '{}'".format(
                    contents[1], value)
    else:
        return _isIp(value)
