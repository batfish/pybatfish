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

__all__ = [
    "BatfishAssertException",
    "BatfishAssertWarning",
    "BatfishException",
    "QuestionValidationException",
]


class BatfishException(Exception):
    """Base exception for Batfish-related errors."""


class BatfishAssertException(BatfishException):
    """Raised if a pybatfish assertion fails.

    .. seealso:: :py:module:`~pybatfish.client.assert`
    """


class BatfishAssertWarning(UserWarning):
    """Used for soft assertions instead of an exception.

    .. seealso:: :py:module:`~pybatfish.client.assert`
    """


class QuestionValidationException(BatfishException):
    """Raised when an invalid Batfish question is encountered."""
