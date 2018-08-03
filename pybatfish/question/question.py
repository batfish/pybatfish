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
import os
import re
import sys
from copy import deepcopy
from inspect import isfunction, getmembers
from typing import Set, Optional, Iterable, List, Dict, Union, Any  # noqa: F401

from six import PY3, integer_types, string_types

from pybatfish.client.commands import (
    bf_logger, bf_session, _bf_answer_obj, _bf_get_question_templates)
from pybatfish.exception import QuestionValidationException
from pybatfish.question import bfq
from pybatfish.util import (validate_question_name,
                            validate_json_path_regex, get_uuid)

# A set of tags across all questions
_tags = set()  # type: Set
_VALID_VARIABLE_NAME_REGEX = re.compile(r'^\w+$')

__all__ = [
    'list_questions',
    'list_tags',
    'load_dir_questions',
    'load_questions',
]


class _QuestionEncoder(json.JSONEncoder):
    """A default encoder for Batfish Question objects."""

    def default(self, obj):
        if isinstance(obj, QuestionBase):
            # Return the dictionary representation of the Question.
            return obj.dict()

        # Fall back to default serialization for all other objects.
        return json.JSONEncoder.default(self, obj)


class QuestionMeta(type):
    """A meta class for all Question classes."""

    def __new__(cls, name, base, dct):
        """Creates a new class for a specific question."""
        new_cls = super(QuestionMeta, cls).__new__(cls, name, base, dct)

        def constructor(self, differential=None, questionName=None,
                        exclusions=None, **kwargs):
            """Create a new question."""
            # Call super (i.e., QuestionBase)
            super(new_cls, self).__init__(new_cls.template)

            # Update well-known params, if passed in
            if differential is not None:
                self._dict['differential'] = differential
            if exclusions is not None:
                self._dict['exclusions'] = exclusions
            if questionName:
                self._dict['instance']['instanceName'] = questionName
            else:
                self._dict['instance']['instanceName'] += \
                    "_" + get_uuid()

            # Validate that we are not accepting invalid kwargs/variables
            instance_vars = self._dict['instance'].get('variables', {})
            print('instance vars: {}'.format(instance_vars))
            var_difference = set(kwargs.keys()).difference(instance_vars)
            if var_difference:
                raise QuestionValidationException(
                    "Received unsupported parameters/variables: {}".format(
                        var_difference))
            # Set question-specific parameters
            for var_name, var_value in kwargs.items():
                instance_vars[var_name]['value'] = var_value

        # Define signature. Helps with tab completion. Python3 centric
        if PY3:
            from inspect import Signature, Parameter
            setattr(constructor, '__signature__', Signature(parameters=[
                Parameter(name=param, kind=Parameter.KEYWORD_ONLY)
                for param in sorted(dct.get("variables", []) +
                                    ['differential', 'questionName'])]))
        setattr(new_cls, '__init__', constructor)
        setattr(new_cls, '__doc__', dct.get("docstring", ""))
        setattr(new_cls, '__module__', dct.get("module", "__main__"))
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

    # TODO: document return values once converged on representation
    def answer(self, snapshot=None, reference_snapshot=None,
               include_one_table_keys=False, background=False):
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

        :raises QuestionValidationException: if the question is malformed
        """
        snapshot = bf_session.get_snapshot(snapshot)
        if reference_snapshot is None and self.getDifferential():
            raise ValueError(
                "reference_snapshot argument is required to answer a differential question")
        _validate(self.dict())
        self.setIncludeOneTableKeys(include_one_table_keys)
        return _bf_answer_obj(self.json(),
                              parameters_str="{}",
                              question_name=self.getName(),
                              background=background,
                              snapshot=snapshot,
                              reference_snapshot=reference_snapshot)

    def dict(self):
        """Return the dictionary representing this question."""
        return self._dict

    def help(self):
        """Display a help message about this question."""
        print(self.__doc__)

    def json(self, **kwargs):
        """Return the json string representing this question.

        Keyword arguments passed to json.dumps with default assignments of
        sort_keys=True and indent=2
        """
        return json.dumps(self._dict, sort_keys=True, indent=2,
                          cls=_QuestionEncoder, **kwargs)

    def load(self, moduleName=bfq.__name__):
        """(Re)load this question as a default question."""
        _load_question_dict(self._dict, module_name=moduleName)

    def getDescription(self):
        """Return the short description of this question."""
        return self._dict['instance']['description']

    def getDifferential(self):
        """Return whether this question is to be asked differentially."""
        if 'differential' in self._dict:
            return self._dict['differential']
        else:
            return False

    def getIncludeOneTableKeys(self):
        """Return whether keys present in only one table should be included when computing answer table diffs."""
        return self._dict.get('includeOneTableKeys', False)

    def getLongDescription(self):
        """Return the long description of this question."""
        return self._dict['instance']['longDescription']

    def getName(self):
        """Return the name of this question."""
        return self._dict['instance']['instanceName']

    def setDescription(self, name):
        """Set the short description of this question.

        You may want to call this before calling 'write' to distinguish this
        question from its parent.
        """
        self._dict['instance']['description'] = name

    def setDifferential(self, differential):
        """Set the differential nature of this question."""
        self._dict['differential'] = differential

    def setIncludeOneTableKeys(self, include_one_table_keys):
        """Set if keys present in only table should be included when computing table diffs."""
        self._dict['includeOneTableKeys'] = include_one_table_keys

    def setLongDescription(self, name):
        """Set the short description of this question.

        You may want to call this before calling 'write' to distinguish this
        question from its parent.
        """
        self._dict['instance']['longDescription'] = name

    def setName(self, name):
        """Set the name of this question.

        Call this before calling 'write' if you want to add a new question
        rather than override/overwrite an existing one.
        """
        self._dict['instance']['instanceName'] = name

    def write(self, path, **kwargs):
        """Write the json file representing this question using the provided name.

        Keyword arguments are passed to json.dumps with default assignments of
        `sort_keys=True` and `indent=2`.
        Be sure to call :py:meth:`setName` first if you want to add a new
        question rather than overwrite an existing one.

        :param path: The path to which to write the output JSON file
        """
        with open(path, 'w') as outputFile:
            outputFile.write(self.json(**kwargs))


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
    desired_tags = set(map(str.lower, tags)) if tags else set()
    question_functions = filter(isfunction, getmembers(module))

    matching_questions = []
    for name, question_func in question_functions:
        if desired_tags and not desired_tags.intersection(
                map(str.lower, question_func.tags)):
            # skip questions that don't have any desired tags
            continue

        matching_questions.append(
            {'name': name,
             'description': question_func.description,
             'tags': question_func.tags
             })
    return matching_questions


def list_tags():
    # type: () -> Set
    """List tags across all available questions."""
    return _tags


def load_dir_questions(questionDir, moduleName=bfq.__name__):
    questionFilenames = []
    for filename in os.listdir(questionDir):
        if filename.endswith(".json"):
            questionFilenames.append(filename)
    localQuestions = set([])
    if len(questionFilenames) == 0:
        bf_logger.warn(
            "WARNING: no .json files found in supplied question directory: {questionDir}".format(
                questionDir=questionDir))
    else:
        numQuestions = 0
        for questionFilename in questionFilenames:
            questionFile = os.path.join(questionDir, questionFilename)
            try:
                localQuestions.add(
                    _load_question_disk(questionFile, module_name=moduleName))
                numQuestions += 1
            except ValueError as err:
                bf_logger.error(
                    "Could not load question from {questionFilename}:{err}".format(
                        questionFilename=questionFilename,
                        err=err))
        bf_logger.info(
            "Successfully loaded {numQuestions}/{numQuestionFiles} question(s) from local directory".format(
                numQuestions=numQuestions,
                numQuestionFiles=len(questionFilenames)))
    return localQuestions


def _load_question_disk(question_path, module_name=bfq.__name__):
    """Load a question template from disk and instantiate a new `:py:class:Question`."""
    with open(question_path, 'r') as question_file:
        question_dict = json.load(question_file)
        return _load_question_dict(question_dict, question_path=question_path,
                                   module_name=module_name)


def _load_question_json(question_str, module_name=bfq.__name__):
    """Load a question template from a valid JSON string and instantiate a new `:py:class:Question`."""
    question = json.loads(question_str)
    return _load_question_dict(question, question_path=None,
                               module_name=module_name)


def _load_question_dict(question, question_path=None, module_name=bfq.__name__):
    # type: (Dict, Optional[str], str) -> str
    """Create a question from a dictionary which contains a template.

    :return the name of the question
    """
    # Perform series of validations on the question.
    # Try to have meaningful error messages.

    # Check has instance data
    instance_data = question.get('instance')
    if not instance_data:
        raise QuestionValidationException(
            "Missing instance data in question (file: {})".format(
                question_path))

    # name validation
    given_question_name = instance_data.get('instanceName')
    if not given_question_name or not validate_question_name(
            given_question_name):
        raise QuestionValidationException(
            "Invalid question name: {}".format(given_question_name))
    question_name = str(given_question_name)  # type: str

    # description validation
    question_description = instance_data.get('description')
    if not question_description:
        raise QuestionValidationException(
            "Missing description for question '{}'".format(question_name))

    # Extend description if we can
    long_description = instance_data.get('longDescription')
    if long_description:
        question_description = "\n".join(
            [question_description, long_description])

    # Extract question tags
    tags = sorted(map(str, instance_data.get('tags', [])))
    _tags.update(tags)

    # Validate question variables
    ivars = instance_data.get('variables')
    variables = _process_variables(question_name, ivars)

    # Compute docstring
    docstring = _compute_docstring(question_description, ivars)

    # Make new Question class and set it in the specified module
    module = sys.modules[module_name]
    setattr(module, question_name,
            QuestionMeta(question_name, (QuestionBase,), {
                'docstring': docstring,
                'description': question_description,
                'module': module_name,
                'tags': tags,
                'template': deepcopy(question),
                'variables': variables,
            }))

    return question_name


def _process_variables(question_name, variables):
    # type: (str, Optional[Dict[str, Dict[str, Any]]]) -> List[str]
    """Perform validation on question variables.

    :returns a sorted list of variable names
    """
    if variables is None:
        return []
    for var_name, var_data in variables.items():
        _validate_variable_name(question_name, var_name)
        _validate_variable_data(question_name, var_name, var_data)
    return sorted(variables.keys())


def _validate_variable_data(question_name, var_name, var_data):
    # type: (str, str, Dict[str, Any]) -> bool
    """Perform validation on variable metadata.

    :raises QuestionValidationException if metadata is invalid.
    """
    if var_data.get('type') is None:
        raise QuestionValidationException(
            "Question {} is missing type for variable {}".format(question_name,
                                                                 var_name))

    if var_data.get('description') is None:
        raise QuestionValidationException(
            "Question {} is missing description for variable {}".format(
                question_name,
                var_name))
    return True


def _validate_variable_name(question_name, var_name):
    # type: (str, str) -> bool
    """Check if the variable name is valid."""
    if not re.match(_VALID_VARIABLE_NAME_REGEX, var_name):
        raise QuestionValidationException(
            "Question {} has invalid variable name: {}. Only alphanumeric characters are allowed".format(
                question_name, var_name))
    return True


def _compute_docstring(base_docstring, variables):
    # type: (str, Optional[Dict[str, Any]]) -> str
    """Compute a docstring for a question, based on the variables."""
    if variables is None:
        return base_docstring
    return "\n".join([base_docstring, "\n"] +
                     [_compute_var_help(*var) for var in variables.items()])


def _compute_var_help(var_name, var_data):
    # type: (str, Dict[str, Any]) -> str
    """Create explanation of a singe question variable."""
    allowed_vals = var_data.get("allowedValues", "")
    default_value = var_data.get("value", "")
    return ":param {name}: {required} {desc}. {allowed} {default}\n:type {name}: {type}\n".format(
        name=var_name,
        type=var_data["type"]
        if 'minElements' not in var_data
        else "list[{}]".format(var_data["type"]),
        required='*Required.*' if not var_data.get('optional', False) else "",
        desc=var_data["description"],
        allowed="\n\n\tAllowed values: ``{}``".format(
            allowed_vals) if allowed_vals else "",
        default="\n\n\tDefault value: ``{}``".format(
            default_value) if default_value else ""
    )


def load_questions(question_dir=None, from_server=False,
                   module_name=bfq.__name__):
    """Load questions from directory or batfish service.

    :param question_dir: Load questions from this local directory instead of
        remote questions from the batfish service.
    :type question_dir: str
    :param from_server: if true, also load questions from service.
        Ignored if `question_dir` is `None`
    :type from_server: bool
    :param module_name: the name of the module where questions should be loaded.
        Default is :py:mod:`pybatfish.question.bfq`
    """
    questions = set()
    over_written_questions = 0
    if not question_dir or from_server:
        remote_questions = _load_remote_questions_templates(
            moduleName=module_name)
        over_written_questions += _merge_questions(remote_questions,
                                                   questions)
    if question_dir:
        local_questions = load_dir_questions(question_dir,
                                             moduleName=module_name)
        over_written_questions += _merge_questions(local_questions,
                                                   questions)
    if over_written_questions > 0:
        bf_logger.info(
            "Overwrote {over_written_questions} remote question(s) with local question(s)".format(
                overWrittenQuestions=over_written_questions))


def _load_remote_questions_templates(moduleName=bfq.__name__):
    numQuestions = 0
    remoteQuestions = set([])
    questionsDict = _bf_get_question_templates()
    for (key, value) in questionsDict.items():
        try:
            remoteQuestions.add(
                _load_question_json(value, module_name=moduleName))
            numQuestions += 1
        except Exception as err:
            bf_logger.error(
                "Could not load question {name} : {err}".format(name=key,
                                                                err=err))
    bf_logger.info(
        "Successfully loaded {numQuestions} questions from remote".format(
            numQuestions=numQuestions))
    return remoteQuestions


def _merge_questions(sourceQuestions, destinationQuestions):
    overWrittenQuestions = 0
    for remoteQuestion in sourceQuestions:
        if remoteQuestion in destinationQuestions:
            overWrittenQuestions += 1
        destinationQuestions.add(remoteQuestion)
    return overWrittenQuestions


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
                                elif 'allowedValues' in variable and valueElement not in \
                                        variable['allowedValues']:
                                    valid = False
                                    errorMessage += "   Value: '" + valueElement + "' is not among allowed values " + json.dumps(
                                        variable[
                                            'allowedValues']) + " of parameter: '" + variableName + "'\n"
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
                    elif 'allowedValues' in variable and \
                                    value not in variable['allowedValues']:
                        valid = False
                        errorMessage += "   Value: '" + value + "' is not among allowed values " + json.dumps(
                            variable[
                                'allowedValues']) + " of parameter: '" + variableName + "'\n"
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
    if expectedType == 'boolean':
        return isinstance(value, bool), None
    elif expectedType == 'comparator':
        validComparators = ['<', '<=', '==', '>=', '>', '!=']
        if value not in validComparators:
            return False, "'{}' is not a known comparator. Valid options are: '{}'".format(
                value,
                ", ".join(validComparators))
        return True, None
    elif expectedType == 'integer':
        INT32_MIN = -2 ** 32
        INT32_MAX = 2 ** 32 - 1
        valid = (isinstance(value, integer_types) and
                 INT32_MIN <= value <= INT32_MAX)
        return valid, None
    elif expectedType == 'float':
        return isinstance(value, float), None
    elif expectedType == 'double':
        return isinstance(value, float), None
    elif expectedType == 'long':
        INT64_MIN = -2 ** 64
        INT64_MAX = 2 ** 64 - 1
        valid = (isinstance(value, integer_types) and
                 INT64_MIN <= value <= INT64_MAX)
        return valid, None
    elif expectedType == 'ip':
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        else:
            return _isIp(value)
    elif expectedType == 'ipWildcard':
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        else:
            return _isIpWildcard(value)
    elif expectedType == 'javaRegex':
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        return True, None
    elif expectedType == 'jsonPath':
        return _isJsonPath(value)
    elif expectedType == 'jsonPathRegex':
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        return validate_json_path_regex(value), None
    elif expectedType == 'prefix':
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        else:
            return _isPrefix(value)
    elif expectedType == 'prefixRange':
        if not isinstance(value, string_types):
            return False, "A Batfish {} must be a string".format(
                expectedType)
        else:
            return _isPrefixRange(value)
    elif expectedType == 'question':
        return isinstance(value, QuestionBase), None
    elif expectedType == 'string':
        return isinstance(value, string_types), None
    elif expectedType == 'subrange':
        if isinstance(value, int):
            return True, None
        elif isinstance(value, string_types):
            return _isSubRange(value)
        else:
            return False, "A Batfish {} must either be a string or an integer".format(
                expectedType)
    elif expectedType == 'protocol':
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
    elif expectedType == 'ipProtocol':
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
