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

import datetime
import json
import logging
from unittest.mock import patch

import pytest
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzlocal
from pytz import UTC

from pybatfish.client import restv2helper
from pybatfish.client.consts import BfConsts
from pybatfish.client.session import Session
from pybatfish.client.workhelper import (
    _format_elapsed_time,
    _parse_timestamp,
    _print_timestamp,
    _print_work_status_helper,
    execute,
)
from pybatfish.client.workitem import WorkItem


def __execute_and_return_request_params(work_item, session, extra_args=None):
    work_item.requestParams[BfConsts.ARG_TESTRIG] = "snapshot"
    with patch.object(restv2helper, "_post") as mock_post:
        execute(work_item, session, True, extra_args)
    args, kwargs = mock_post.call_args
    witem = args[2]
    return witem["requestParams"]


def test_execute_request_params():
    session = Session(load_questions=False)

    # Unmodified work item
    work_item = WorkItem(session)
    witem = __execute_and_return_request_params(work_item, session)
    assert "TESTARG" not in witem

    session.additional_args["TESTARG"] = "addl"

    # Work item with additional args
    work_item = WorkItem(session)
    witem = __execute_and_return_request_params(work_item, session)
    assert witem.get("TESTARG") == "addl"

    # Work item with additional args and extra args
    work_item = WorkItem(session)
    witem = __execute_and_return_request_params(
        work_item, session, extra_args={"TESTARG": "extra"}
    )
    assert witem.get("TESTARG") == "extra"

    # Confirm additional args not messed up
    work_item = WorkItem(session)
    witem = __execute_and_return_request_params(work_item, session)
    assert witem.get("TESTARG") == "addl"


def test_format_elapsed_time():
    delta1 = relativedelta(
        years=7, months=6, days=5, hours=4, minutes=3, seconds=2, microsecond=1
    )
    ref1 = "7y6m5d04:03:02"
    assert _format_elapsed_time(delta1) == ref1
    delta2 = relativedelta(
        months=6, days=5, hours=4, minutes=3, seconds=2, microsecond=1
    )
    ref2 = "6m5d04:03:02"
    assert _format_elapsed_time(delta2) == ref2
    delta3 = relativedelta(days=5, hours=4, minutes=3, seconds=2, microsecond=1)
    ref3 = "5d04:03:02"
    assert _format_elapsed_time(delta3) == ref3
    delta4 = relativedelta(hours=4, minutes=3, seconds=2, microsecond=1)
    ref4 = "04:03:02"
    assert _format_elapsed_time(delta4) == ref4
    delta5 = relativedelta(minutes=3, seconds=2, microsecond=1)
    ref5 = "00:03:02"
    assert _format_elapsed_time(delta5) == ref5
    delta6 = relativedelta(seconds=2, microsecond=1)
    ref6 = "00:00:02"
    assert _format_elapsed_time(delta6) == ref6
    delta7 = relativedelta(microsecond=1)
    ref7 = "00:00:00"
    assert _format_elapsed_time(delta7) == ref7


def test_parse_numeric_timestamp():
    # When older versions of Batfish sent numeric timestamps, they were in
    # server's local time.
    s = "1511981483456"
    ref = datetime.datetime(2017, 11, 29, 18, 51, 23, 456000)
    assert _parse_timestamp(s) == ref


def test_parse_rfc3339_timestamp():
    s = "2017-11-29T18:51:23.456+0000"
    ref = datetime.datetime(2017, 11, 29, 18, 51, 23, 456000, tzinfo=UTC)
    assert _parse_timestamp(s) == ref


def test_print_timestamp():
    ref = datetime.datetime(2017, 11, 29, 18, 51, 23, 456000, tzinfo=UTC)
    assert _print_timestamp(ref) == ref.astimezone(tzlocal()).isoformat(" ")


def test_print_workstatus_fresh_task(caplog):
    session = Session(load_questions=False)
    session.stale_timeout = 5
    nowFunction = lambda tzinfo: datetime.datetime(
        2017, 12, 20, 0, 0, 0, 0, tzinfo=tzinfo
    )
    workStatus = "TEST"
    taskDetails = json.dumps(
        {
            "obtained": "2017-12-20 00:00:00 UTC",
            "batches": [
                {
                    "completed": 0,
                    "description": "Fooing the bar",
                    "size": 0,
                    "startDate": "2017-12-20 00:00:00 UTC",
                }
            ],
        }
    )
    with caplog.at_level(logging.DEBUG):
        _print_work_status_helper(session, workStatus, taskDetails, nowFunction)
    assert "status: TEST" in caplog.text
    assert (
        ".... {obtained} Fooing the bar".format(
            obtained=_print_timestamp(
                _parse_timestamp(json.loads(taskDetails)["obtained"])
            )
        )
        in caplog.text
    )


def test_print_workstatus_fresh_task_subtasks(caplog):
    session = Session(load_questions=False)
    session.stale_timeout = 5
    nowFunction = lambda tzinfo: datetime.datetime(
        2017, 12, 20, 0, 0, 0, 0, tzinfo=tzinfo
    )
    workStatus = "TEST"
    taskDetails = json.dumps(
        {
            "obtained": "2017-12-20 00:00:00 UTC",
            "batches": [
                {
                    "completed": 1,
                    "description": "Fooing the bar",
                    "size": 2,
                    "startDate": "2017-12-20 00:00:00 UTC",
                }
            ],
        }
    )
    with caplog.at_level(logging.DEBUG):
        _print_work_status_helper(session, workStatus, taskDetails, nowFunction)
    assert "status: TEST" in caplog.text
    assert (
        ".... {obtained} Fooing the bar 1 / 2.".format(
            obtained=_print_timestamp(
                _parse_timestamp(json.loads(taskDetails)["obtained"])
            )
        )
        in caplog.text
    )


def test_print_workstatus_old_task(caplog):
    session = Session(load_questions=False)
    session.stale_timeout = 5
    nowFunction = lambda tzinfo: datetime.datetime(
        2017, 12, 20, 0, 0, 0, 0, tzinfo=tzinfo
    )
    workStatus = "TEST"
    taskDetails = json.dumps(
        {
            "obtained": "2016-11-22 10:43:21 UTC",
            "batches": [
                {
                    "completed": 0,
                    "description": "Fooing the bar.",
                    "size": 0,
                    "startDate": "2016-11-22 10:43:22 UTC",
                }
            ],
        }
    )
    with caplog.at_level(logging.DEBUG):
        _print_work_status_helper(session, workStatus, taskDetails, nowFunction)
    assert "status: TEST" in caplog.text
    assert (
        ".... {obtained} Fooing the bar. (1y27d13:16:39 elapsed)".format(
            obtained=_print_timestamp(
                _parse_timestamp(json.loads(taskDetails)["obtained"])
            )
        )
        in caplog.text
    )


def test_print_workstatus_old_task_subtasks(caplog):
    session = Session(load_questions=False)
    session.stale_timeout = 5
    nowFunction = lambda tzinfo: datetime.datetime(
        2017, 12, 20, 0, 0, 0, 0, tzinfo=tzinfo
    )
    workStatus = "TEST"
    taskDetails = json.dumps(
        {
            "obtained": "2016-11-22 10:43:21 UTC",
            "batches": [
                {
                    "completed": 1,
                    "description": "Fooing the bar",
                    "size": 2,
                    "startDate": "2016-11-22 10:43:22 UTC",
                }
            ],
        }
    )
    with caplog.at_level(logging.DEBUG):
        _print_work_status_helper(session, workStatus, taskDetails, nowFunction)
    assert "status: TEST" in caplog.text
    assert (
        ".... {obtained} Fooing the bar 1 / 2. (1y27d13:16:39 elapsed)".format(
            obtained=_print_timestamp(
                _parse_timestamp(json.loads(taskDetails)["obtained"])
            )
        )
        in caplog.text
    )


if __name__ == "__main__":
    pytest.main()
