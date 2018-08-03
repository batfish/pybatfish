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
"""A collection of functions that execute RPCs against a Batfish server."""

from __future__ import absolute_import, print_function

import datetime
import json
import logging
import time
from typing import Dict, Optional, Any  # noqa: F401

import six
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzlocal

from pybatfish.client.consts import BfConsts, WorkStatusCode, CoordConsts
from pybatfish.client.session import Session  # noqa: F401
from pybatfish.exception import BatfishException
from . import resthelper
from .workitem import WorkItem  # noqa: F401


def _batch_to_string(json_batch, elapsed):
    # type: (Dict, Optional[relativedelta]) -> str
    """Get status of the Batfish job batch."""
    description = json_batch["description"]
    elapsed_str = " Elapsed %s" % _format_elapsed_time(elapsed) \
        if elapsed is not None else ""
    if json_batch["size"] == 0:
        return "{desc}{elapsed}".format(desc=description, elapsed=elapsed_str)
    else:
        return "{desc} {completed} / {size}{elapsed}" \
            .format(desc=description, completed=json_batch['completed'],
                    size=json_batch['size'], elapsed=elapsed_str)


def _parse_timestamp(timestamp_str):
    # type: (str) -> datetime.datetime
    """Convert the given Batfish date string into a printable local time."""
    try:
        # Attempt to parse a Unix timestamp in milliseconds
        millis = int(timestamp_str)
        return datetime.datetime(1970, 1, 1) + datetime.timedelta(
            milliseconds=millis)
    except ValueError:
        # Parse a RFC 3339 timestamp
        return parse(timestamp_str)


def _print_timestamp(timestamp):
    # type: (datetime.datetime) -> str
    # Print the timestamp in the appropriate locale
    return timestamp.astimezone(tzlocal()).strftime("%c %Z")


def execute(work_item, session, background=False):
    # type: (WorkItem, Session, bool) -> Dict[str, str]
    """Submit a work item to Batfish.

    :param work_item: work to submit
    :type work_item: :py:class:`~pybatfish.client.WorkItem`
    :param session: Batfish session to use.
    :type session: :py:class:`~pybatfish.client.session.Session`
    :param background: Whether to background the job. If `True`,
        this function only returns the result of submitting the job.
    :type background: bool

    :return: If `background=True`, a dict containing a single key 'result' with
    a string description of the result. If `background=False`, a dict containing
    "status" and "answer" keys, both strings.
    """
    json_data = {CoordConsts.SVC_KEY_WORKITEM: work_item.to_json(),
                 CoordConsts.SVC_KEY_API_KEY: session.apiKey}

    # Submit the work item
    response = resthelper.get_json_response(
        session, CoordConsts.SVC_RSC_QUEUE_WORK, json_data)

    if background:
        return {"result": str(response["result"])}

    try:
        answer = get_work_status(work_item.id, session)
        status = WorkStatusCode(answer[CoordConsts.SVC_KEY_WORKSTATUS])
        task_details = answer[CoordConsts.SVC_KEY_TASKSTATUS]

        while not WorkStatusCode.is_terminated(status):
            print_work_status(session, status, task_details)
            time.sleep(1)
            answer = get_work_status(work_item.id, session)
            status = WorkStatusCode(answer[CoordConsts.SVC_KEY_WORKSTATUS])
            task_details = answer[CoordConsts.SVC_KEY_TASKSTATUS]

        print_work_status(session, status, task_details)

        if status == WorkStatusCode.ASSIGNMENTERROR:
            raise BatfishException(
                "Work finished with status {}\n{}".format(status,
                                                          work_item.to_json()))

        # get the answer
        answer_file_name = _compute_batfish_answer_file_name(work_item)
        answer_bytes = resthelper.get_object(session, answer_file_name)

        # In Python 3.x, answer needs to be decoded before it can be used
        # for things like json.loads (<= 3.6).
        if six.PY3:
            answer_string = answer_bytes.decode(encoding="utf-8")
        else:
            answer_string = answer_bytes
        return {"status": status, "answer": answer_string}

    except KeyboardInterrupt:
        response = kill_work(session, work_item.id)
        raise KeyboardInterrupt(
            "Killed ongoing work: {}. Server response: {}".format(
                work_item.id, json.dumps(response)))


def _compute_batfish_answer_file_name(work_item):
    # type: (WorkItem) -> str
    """Return the answer filename as Batfish computes it."""
    return work_item.id + BfConsts.SUFFIX_ANSWER_JSON_FILE


def _format_elapsed_time(delta):
    return "{years}{months}{days}{hours}:{minutes}:{seconds}".format(
        years="%dy" % delta.years if delta.years else "",
        months="%dm" % delta.months if delta.months else "",
        days="%dd" % delta.days if delta.days else "",
        hours="%02d" % delta.hours,
        minutes="%02d" % delta.minutes,
        seconds="%02d" % delta.seconds)


def get_data_upload_question(session, question_name, question_json,
                             parameters_json):
    # type: (Session, str, str, str) -> Dict
    """Create the form parameters needed to upload the given question."""
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_CONTAINER_NAME: session.network,
                 CoordConsts.SVC_KEY_QUESTION_NAME: question_name,
                 CoordConsts.SVC_KEY_FILE: ('question', question_json),
                 CoordConsts.SVC_KEY_FILE2: ('parameters', parameters_json)}
    return json_data


def get_data_auto_complete(session, completion_type, query, max_suggestions):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_CONTAINER_NAME: session.network,
                 CoordConsts.SVC_KEY_TESTRIG_NAME: session.baseSnapshot,
                 CoordConsts.SVC_KEY_COMPLETION_TYPE: completion_type,
                 CoordConsts.SVC_KEY_QUERY: query}
    if max_suggestions:
        json_data[CoordConsts.SVC_KEY_MAX_SUGGESTIONS] = max_suggestions
    return json_data


def get_data_configure_analysis(session, new_analysis, analysis_name,
                                add_questions_filename, del_questions_str):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_CONTAINER_NAME: session.network}
    if new_analysis:
        json_data[CoordConsts.SVC_KEY_NEW_ANALYSIS] = "new"
    json_data[CoordConsts.SVC_KEY_ANALYSIS_NAME] = analysis_name
    if add_questions_filename:
        json_data[CoordConsts.SVC_KEY_FILE] = (
            'filename', open(add_questions_filename, 'rb'),
            'application/octet-stream')
    if del_questions_str:
        json_data[
            CoordConsts.SVC_KEY_DEL_ANALYSIS_QUESTIONS] = del_questions_str
    return json_data


def get_data_configure_question_template(session, in_question, exceptions,
                                         assertion):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_QUESTION: in_question}
    if exceptions:
        json_data[CoordConsts.SVC_KEY_EXCEPTIONS] = json.dumps(exceptions)
    if assertion:
        json_data[CoordConsts.SVC_KEY_ASSERTION] = json.dumps(
            assertion.__dict__)
    return json_data


def get_data_delete_analysis(session, analysis_name):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_CONTAINER_NAME: session.network,
                 CoordConsts.SVC_KEY_ANALYSIS_NAME: analysis_name}
    return json_data


def get_data_delete_network(session, name):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_NETWORK_NAME: name}
    return json_data


def get_data_delete_snapshot(session, name):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_NETWORK_NAME: session.network,
                 CoordConsts.SVC_KEY_SNAPSHOT_NAME: name}
    return json_data


def get_data_get_analysis_answers(session, analysis_name, snapshot,
                                  reference_snapshot=None):
    # type: (Session, str, str, Optional[str]) -> Dict
    json_data = {
        CoordConsts.SVC_KEY_API_KEY: session.apiKey,
        CoordConsts.SVC_KEY_CONTAINER_NAME: session.network,
        CoordConsts.SVC_KEY_TESTRIG_NAME: snapshot,
        CoordConsts.SVC_KEY_ENV_NAME: BfConsts.RELPATH_DEFAULT_ENVIRONMENT_NAME,
    }
    if reference_snapshot is not None:
        json_data[CoordConsts.SVC_KEY_DELTA_TESTRIG_NAME] = reference_snapshot
        json_data[
            CoordConsts.SVC_KEY_DELTA_ENV_NAME] = BfConsts.RELPATH_DEFAULT_ENVIRONMENT_NAME
    json_data[CoordConsts.SVC_KEY_ANALYSIS_NAME] = analysis_name
    return json_data


def _get_data_get_question_templates(session):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey}
    return json_data


def get_data_get_answer(session, question_name, snapshot,
                        reference_snapshot=None):
    # type: (Session, str, str, Optional[str]) -> Dict
    json_data = {
        CoordConsts.SVC_KEY_API_KEY: session.apiKey,
        CoordConsts.SVC_KEY_CONTAINER_NAME: session.network,
        CoordConsts.SVC_KEY_TESTRIG_NAME: snapshot,
        CoordConsts.SVC_KEY_ENV_NAME: BfConsts.RELPATH_DEFAULT_ENVIRONMENT_NAME,
        CoordConsts.SVC_KEY_QUESTION_NAME: question_name,
    }
    if reference_snapshot is not None:
        json_data[CoordConsts.SVC_KEY_DELTA_TESTRIG_NAME] = reference_snapshot
        json_data[
            CoordConsts.SVC_KEY_DELTA_ENV_NAME] = BfConsts.RELPATH_DEFAULT_ENVIRONMENT_NAME
    return json_data


def get_data_init_network(session, network_name, network_prefix):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_NETWORK_NAME: network_name,
                 CoordConsts.SVC_KEY_NETWORK_PREFIX: network_prefix}
    return json_data


def get_data_kill_work(session, workId):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_WORKID: workId}
    return json_data


def get_data_list_analyses(session):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_CONTAINER_NAME: session.network}
    return json_data


def get_data_list_networks(session):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey}
    return json_data


def get_data_list_incomplete_work(session):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_CONTAINER_NAME: session.network}
    return json_data


def get_data_list_questions(session):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_CONTAINER_NAME: session.network}
    return json_data


def get_data_list_snapshots(session, network):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey}
    if network is not None:
        json_data[CoordConsts.SVC_KEY_NETWORK_NAME] = network
    return json_data


def get_data_list_testrigs(session, network):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey}
    if network is not None:
        json_data[CoordConsts.SVC_KEY_CONTAINER_NAME] = network
    return json_data


def get_data_sync_snapshots_sync_now(session, plugin_id, force):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_NETWORK_NAME: session.network,
                 CoordConsts.SVC_KEY_PLUGIN_ID: plugin_id,
                 CoordConsts.SVC_KEY_FORCE: str(force)}
    return json_data


def get_data_sync_snapshots_update_settings(session, plugin_id, settings_dict):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_NETWORK_NAME: session.network,
                 CoordConsts.SVC_KEY_PLUGIN_ID: plugin_id,
                 CoordConsts.SVC_KEY_SETTINGS: json.dumps(settings_dict)}
    return json_data


def get_data_upload_snapshot(session, snapshot, file_to_send):
    # type: (Session, str, str) -> Dict
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_NETWORK_NAME: session.network,
                 CoordConsts.SVC_KEY_SNAPSHOT_NAME: snapshot,
                 CoordConsts.SVC_KEY_ZIPFILE: (
                     'filename', open(file_to_send, 'rb'),
                     'application/octet-stream')}
    return json_data


def get_workitem_answer(session, question_name, snapshot,
                        reference_snapshot=None):
    # type: (Session, str, str, Optional[str]) -> WorkItem
    """Return the result of submitting a question as a WorkItem."""
    work_item = WorkItem(session)

    parameters = {
        BfConsts.COMMAND_ANSWER: "",
        BfConsts.ARG_QUESTION_NAME: question_name,
        BfConsts.ARG_TESTRIG: snapshot,
        BfConsts.ARG_ENVIRONMENT_NAME: BfConsts.RELPATH_DEFAULT_ENVIRONMENT_NAME,
    }

    if reference_snapshot is not None:
        parameters[BfConsts.ARG_DELTA_TESTRIG] = reference_snapshot
        parameters[
            BfConsts.ARG_DELTA_ENVIRONMENT_NAME] = BfConsts.RELPATH_DEFAULT_ENVIRONMENT_NAME
        parameters[BfConsts.ARG_DIFFERENTIAL] = ""

    work_item.requestParams.update(parameters)

    return work_item


def get_workitem_generate_dataplane(session, snapshot):
    # type: (Session, str) -> WorkItem
    w_item = WorkItem(session)
    w_item.requestParams[BfConsts.COMMAND_DUMP_DP] = ""
    w_item.requestParams[BfConsts.ARG_TESTRIG] = snapshot
    w_item.requestParams[
        BfConsts.ARG_ENVIRONMENT_NAME] = BfConsts.RELPATH_DEFAULT_ENVIRONMENT_NAME
    return w_item


def get_workitem_parse(session, snapshot):
    # type: (Session, str) -> WorkItem
    w_item = WorkItem(session)
    w_item.requestParams[BfConsts.ARG_TESTRIG] = snapshot
    w_item.requestParams[BfConsts.COMMAND_PARSE_VENDOR_INDEPENDENT] = ""
    w_item.requestParams[BfConsts.COMMAND_PARSE_VENDOR_SPECIFIC] = ""
    w_item.requestParams[BfConsts.COMMAND_INIT_INFO] = ""
    return w_item


def get_workitem_run_analysis(session, analysis_name, snapshot,
                              reference_snapshot=None):
    # type: (Session, str, str, Optional[str]) -> WorkItem
    w_item = WorkItem(session)
    w_item.requestParams[BfConsts.COMMAND_ANALYZE] = ""
    w_item.requestParams[BfConsts.ARG_ANALYSIS_NAME] = analysis_name
    w_item.requestParams[BfConsts.ARG_TESTRIG] = snapshot
    w_item.requestParams[
        BfConsts.ARG_ENVIRONMENT_NAME] = BfConsts.RELPATH_DEFAULT_ENVIRONMENT_NAME
    if reference_snapshot is not None:
        w_item.requestParams[BfConsts.ARG_DELTA_TESTRIG] = reference_snapshot
        w_item.requestParams[
            BfConsts.ARG_DELTA_ENVIRONMENT_NAME] = BfConsts.RELPATH_DEFAULT_ENVIRONMENT_NAME
        w_item.requestParams[BfConsts.ARG_DIFFERENTIAL] = ""
    return w_item


def get_work_status(w_item_id, session):
    json_data = {CoordConsts.SVC_KEY_API_KEY: session.apiKey,
                 CoordConsts.SVC_KEY_WORKID: w_item_id}

    answer = resthelper.get_json_response(session,
                                          CoordConsts.SVC_RSC_GET_WORKSTATUS,
                                          json_data)

    if CoordConsts.SVC_KEY_WORKSTATUS in answer:
        return answer
    else:
        raise BatfishException(
            "Expected key (%s) not found in status check response: %s" %
            (CoordConsts.SVC_KEY_WORKSTATUS,
             answer))


def kill_work(session, w_item_id):
    json_data = get_data_kill_work(session, w_item_id)
    return resthelper.get_json_response(session, CoordConsts.SVC_RSC_KILL_WORK,
                                        json_data)


def print_work_status(session, work_status, task_details):
    # type: (Session, WorkStatusCode, str) -> Any
    return _print_work_status(session, work_status, task_details,
                              datetime.datetime.now)


def _print_work_status(session, work_status, task_details, now_function):
    if session.logger.getEffectiveLevel() == logging.INFO \
            or session.logger.getEffectiveLevel() == logging.DEBUG:
        session.logger.info("status: {}".format(work_status))

        json_task = json.loads(task_details)
        if not json_task:
            session.logger.info(".... no task information")
            return
        obtained_time = _parse_timestamp(json_task["obtained"])
        now = now_function(obtained_time.tzinfo)
        obtained_str = _print_timestamp(obtained_time)
        batches = json_task["batches"] if "batches" in json_task else []

        if batches:
            # when log level is INFO, we only print the last batch
            # else print all
            lastbatch = batches[-1]
            batch_started_time = _parse_timestamp(lastbatch["startDate"])
            batch_elapsed = relativedelta(now, batch_started_time)
            batch_elapsed_seconds = (now - batch_started_time).total_seconds()
            print_batch_elapsed = batch_elapsed_seconds > session.elapsed_delay
            for batch in batches[:-1]:
                session.logger.debug(".... {obtained_time} {batch}".format(
                    obtained_time=obtained_str,
                    batch=_batch_to_string(batch, None)))
            session.logger.info(
                ".... {obtained_time} {batch}".format(
                    obtained_time=obtained_str,
                    batch=_batch_to_string(
                        lastbatch,
                        batch_elapsed if print_batch_elapsed else None)))
