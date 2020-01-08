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
"""Contains internal functions for interacting with the Batfish service."""

import json
from typing import Any, Dict, Optional, TYPE_CHECKING, Union  # noqa: F401

from pybatfish.client import restv2helper
from pybatfish.client.consts import CoordConsts
from pybatfish.datamodel.answer import Answer  # noqa: F401
from pybatfish.util import get_uuid
from . import resthelper, workhelper
from .options import Options

if TYPE_CHECKING:
    from pybatfish.client.session import Session  # noqa: F401


def _bf_answer_obj(
    session,
    question_str,
    parameters_str,
    question_name,
    background,
    snapshot,
    reference_snapshot,
    extra_args,
):
    # type: (Session, str, str, str, bool, str, Optional[str], Optional[Dict[str, Any]]) -> Union[Answer, str]
    json.loads(parameters_str)  # a syntactic check for parametersStr
    if not question_name:
        question_name = Options.default_question_prefix + "_" + get_uuid()

    # Upload the question
    json_data = workhelper.get_data_upload_question(
        session, question_name, question_str, parameters_str
    )
    resthelper.get_json_response(
        session, CoordConsts.SVC_RSC_UPLOAD_QUESTION, json_data
    )

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
