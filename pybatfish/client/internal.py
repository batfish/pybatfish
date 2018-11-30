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
from typing import Dict, Optional, Union  # noqa: F401

import six

from pybatfish.client.consts import CoordConsts
from pybatfish.datamodel import answer
from pybatfish.util import (get_uuid)
from . import resthelper, workhelper
from .options import Options
from .workhelper import _get_data_get_question_templates


def _bf_answer_obj(question_str, parameters_str, question_name,
                   background, snapshot, reference_snapshot):
    # type: (str, str, str, bool, str, Optional[str]) -> Union[str, Dict]
    from pybatfish.client.commands import bf_session

    json.loads(parameters_str)  # a syntactic check for parametersStr
    if not question_name:
        question_name = Options.default_question_prefix + "_" + get_uuid()

    # Upload the question
    json_data = workhelper.get_data_upload_question(bf_session, question_name,
                                                    question_str,
                                                    parameters_str)
    resthelper.get_json_response(bf_session,
                                 CoordConsts.SVC_RSC_UPLOAD_QUESTION, json_data)

    # Answer the question
    work_item = workhelper.get_workitem_answer(bf_session, question_name,
                                               snapshot, reference_snapshot)
    workhelper.execute(work_item, bf_session, background)

    if background:
        return work_item.id

    # get the answer
    answer_bytes = resthelper.get_answer(bf_session, snapshot, question_name,
                                         reference_snapshot)

    # In Python 3.x, answer needs to be decoded before it can be used
    # for things like json.loads (<= 3.6).
    if six.PY3:
        answer_string = answer_bytes.decode(encoding="utf-8")
    else:
        answer_string = answer_bytes
    answer_obj = json.loads(answer_string)

    return answer.from_string(answer_obj[1]['answer'])


def _bf_get_question_templates():
    from pybatfish.client.commands import bf_session
    jsonData = _get_data_get_question_templates(bf_session)
    jsonResponse = resthelper.get_json_response(bf_session,
                                                CoordConsts.SVC_RSC_GET_QUESTION_TEMPLATES,
                                                jsonData)
    return jsonResponse[CoordConsts.SVC_KEY_QUESTION_LIST]
