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

from typing import Any, Dict, Union  # noqa: F401

from pybatfish.datamodel.answer.base import Answer
from pybatfish.datamodel.answer.table import TableAnswer

__all__ = ['from_dict', 'Answer', 'TableAnswer']


def from_dict(dict):
    # type: (Dict[str, Any]) -> Union[Answer, TableAnswer]
    """Take a dict representing a Batfish answer, return answer object.

    :returns either an old :py:class:`Answer`
        or new :py:class:`TableAnswer` class.
    """
    if "answerElements" in dict and "metadata" in dict["answerElements"][0]:
        return TableAnswer(dict)
    else:
        return Answer(dict)
