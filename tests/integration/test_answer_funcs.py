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
import typing
from os.path import abspath, dirname, join, pardir, realpath

import pytest

from pybatfish.client.session import Session
from pybatfish.datamodel.flow import HeaderConstraints
from pybatfish.exception import BatfishException

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))
TEST_NETWORK = "ref_network"
TEST_NETWORK_TR = "ref_network_tr"


@pytest.fixture(scope="module")
def bf() -> Session:
    return Session()


@pytest.fixture(scope="module")
def network(bf: Session) -> typing.Generator[str, None, None]:
    try:
        bf.delete_network(TEST_NETWORK)
    except Exception:
        pass
    bf.set_network(TEST_NETWORK)
    yield bf.init_snapshot(join(_this_dir, "snapshot"), name="snapshot")
    bf.delete_network(TEST_NETWORK)


@pytest.fixture(scope="module")
def traceroute_network(bf: Session) -> typing.Generator[str, None, None]:
    try:
        bf.delete_network(TEST_NETWORK_TR)
    except Exception:
        pass
    bf.set_network(TEST_NETWORK_TR)
    yield bf.init_snapshot(join(_this_dir, "tracert_snapshot"), name="snapshot_tracert")
    bf.delete_network(TEST_NETWORK_TR)


def test_answer_background(bf: Session, network: str) -> None:
    """Expect a GUID when running in background, which can be fed to bf.get_work_status."""
    work_item_id = bf.q.ipOwners().answer(background=True)  # type: ignore
    bf.get_work_status(work_item_id)


def test_answer_foreground(bf: Session, network: str) -> None:
    """Expect an answer that is valid JSON when run in foreground."""
    bf.q.ipOwners().answer()  # type: ignore


def test_answer_fail(bf: Session, network: str) -> None:
    """Expect a BatfishException with searchFilters specifying a non-existant filter."""
    with pytest.raises(BatfishException) as err:
        bf.q.searchFilters(filters="undefined").answer().frame()  # type: ignore
    assert "Work terminated abnormally" in str(err.value)


def test_answer_traceroute(bf: Session, traceroute_network: str) -> None:
    answer = (
        bf.q.traceroute(  # type: ignore
            startLocation="hop1", headers=HeaderConstraints(dstIps="1.0.0.2")
        )
        .answer(extra_args={"debugflags": "traceroute"})
        .frame()
    )
    list_traces = answer.iloc[0]["Traces"]
    assert len(list_traces) == 1
    trace = list_traces[0]
    assert trace.disposition == "ACCEPTED"
    hops = trace.hops
    assert len(hops) == 2
    assert hops[-1].steps[-1].action == "ACCEPTED"
