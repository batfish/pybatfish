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

import pytest

from pybatfish.exception import QuestionValidationException
from pybatfish.util import conditional_str, validate_name, \
    validate_question_name


def test_conditional_str():
    prefix = 'pre'
    suffix = 'after'
    s = conditional_str(prefix, [], suffix)
    assert s == ""
    s = conditional_str(prefix, {}, suffix)
    assert s == ""
    s = conditional_str(prefix, set(), suffix)
    assert s == ""
    s = conditional_str(prefix, None, suffix)
    assert s == ""
    s = conditional_str(prefix, [{}], suffix)
    assert s == "pre [{}] after"
    s = conditional_str(prefix, ['hey'], suffix)
    assert s == "pre ['hey'] after"


def test_validate_name():
    assert validate_name('goodname')
    for name in [42, 'x' * 151, '/', '/etc', 'seTTings', 'settings', ".",
                 "../../../../etc/"]:
        with pytest.raises(ValueError):
            assert validate_name(name)

    for name in ["23", '___', 'foo-bar']:
        validate_name(name)


def test_validate_question_name():
    assert validate_name('goodname')
    for name in [42, 'x' * 151, '/', '/etc']:
        with pytest.raises(QuestionValidationException):
            assert validate_question_name(name)
