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

import json

from pybatfish.datamodel.answer.base import Answer
from pybatfish.datamodel.answer.table import TableAnswer

__all__ = ['from_string', 'Answer', 'TableAnswer']


def from_string(json_string):
    # type: (str) -> Answer
    """Take a string representing a Batfish answer, return answer object.

    :returns either an old :py:class:`Answer`
        or new :py:class:`TableAnswer` class.
    """
    o = json.loads(json_string)
    if "answerElements" in o and "metadata" in o["answerElements"][0]:
        return TableAnswer(o)
    else:
        return Answer(o)
