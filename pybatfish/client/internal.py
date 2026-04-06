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
"""Contains internal functions for interacting with the Batfish service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pybatfish.client import restv2helper

if TYPE_CHECKING:
    from pybatfish.client.session import Session


def _bf_get_question_templates(session: Session, verbose: bool = False) -> dict:
    return restv2helper.get_question_templates(session, verbose)
