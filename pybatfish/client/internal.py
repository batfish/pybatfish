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

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from pybatfish.client import restv2helper
from pybatfish.datamodel.answer import Answer
from pybatfish.util import get_uuid

from . import workhelper
from .options import Options

if TYPE_CHECKING:
    from pybatfish.client.session import Session


def _bf_answer_obj(
    session: "Session",
    question_str: str,
    question_name: str,
    background: bool,
    snapshot: str,
    reference_snapshot: Optional[str],
    extra_args: Optional[Dict[str, Any]],
) -> Union[Answer, str]:
    if not question_name:
        question_name = Options.default_question_prefix + "_" + get_uuid()

    # Upload the question
    restv2helper.upload_question(session, question_name, question_str)

    # Answer the question
    work_item = workhelper.get_workitem_answer(
        session, question_name, snapshot, reference_snapshot
    )
    workhelper.execute(work_item, session, background, extra_args)

    if background:
        return work_item.id

    # get the answer
    return session.get_answer(question_name, snapshot, reference_snapshot)


def _bf_get_question_templates(session: "Session", verbose: bool = False) -> Dict:
    return restv2helper.get_question_templates(session, verbose)
