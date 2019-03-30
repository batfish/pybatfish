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

from os.path import abspath, dirname, join, pardir, realpath

import pytest

from pybatfish.client.commands import (bf_delete_network, bf_get_work_status,
                                       bf_init_analysis, bf_init_snapshot,
                                       bf_session, bf_set_network)
from pybatfish.datamodel.flow import HeaderConstraints
from pybatfish.exception import BatfishException
from pybatfish.question import bfq
from pybatfish.question.question import load_questions

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))
_stable_question_dir = abspath(join(_root_dir, 'questions', 'stable'))
_experimental_question_dir = abspath(
    join(_root_dir, 'questions', 'experimental'))
TEST_NETWORK = 'ref_network'


@pytest.fixture(scope='module')
def network():
    load_questions(_stable_question_dir)
    load_questions(_experimental_question_dir)
    try:
        bf_delete_network(TEST_NETWORK)
    except Exception:
        pass
    bf_set_network(TEST_NETWORK)
    yield bf_init_snapshot(join(_this_dir, "snapshot"), name="snapshot")
    bf_delete_network(TEST_NETWORK)


@pytest.fixture(scope='module')
def traceroute_network():
    load_questions(_stable_question_dir)
    load_questions(_experimental_question_dir)
    try:
        bf_delete_network(TEST_NETWORK)
    except Exception:
        pass
    bf_set_network(TEST_NETWORK)
    yield bf_init_snapshot(join(_this_dir, "tracert_snapshot"),
                           name="snapshot_tracert")
    bf_delete_network(TEST_NETWORK)


def test_answer_background(network):
    """Expect a GUID when running in background, which can be fed to bf_get_work_status."""
    work_item_id = bfq.ipOwners().answer(background=True)
    bf_get_work_status(work_item_id)


def test_answer_foreground(network):
    """Expect an answer that is valid JSON when run in foreground."""
    bfq.ipOwners().answer()


def test_answer_fail(network):
    """Expect a BatfishException with searchFilters specifying a non-existant filter."""
    with pytest.raises(BatfishException) as err:
        bfq.searchFilters(filters="undefined").answer().frame()
    assert "Work terminated abnormally" in str(err.value)


def test_init_analysis(network):
    """Ensure bf_init_analysis does not crash."""
    bf_init_analysis("test_analysis", _stable_question_dir)


def test_answer_traceroute(traceroute_network):
    bf_session.additional_args = {'debugflags': 'traceroute'}
    answer = bfq.traceroute(startLocation="hop1", headers=HeaderConstraints(
        dstIps="1.0.0.2")).answer().frame()
    list_traces = answer.iloc[0]['Traces']
    assert len(list_traces) == 1
    trace = list_traces[0]
    assert trace.disposition == "ACCEPTED"
    hops = trace.hops
    assert len(hops) == 2
    assert hops[-1].steps[-1].action == 'ACCEPTED'
