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
from unittest.mock import patch

import pandas as pd
import pytest
from pandas import DataFrame

from pybatfish.client.asserts import (
    UNESTABLISHED_OSPF_SESSION_STATUS_SPEC,
    _format_df,
    _get_question_object,
    _is_dict_match,
    _raise_common,
    assert_filter_denies,
    assert_filter_has_no_unreachable_lines,
    assert_filter_permits,
    assert_flows_fail,
    assert_flows_succeed,
    assert_has_no_route,
    assert_has_route,
    assert_no_duplicate_router_ids,
    assert_no_forwarding_loops,
    assert_no_incompatible_bgp_sessions,
    assert_no_incompatible_ospf_sessions,
    assert_no_undefined_references,
    assert_no_unestablished_bgp_sessions,
)
from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints, PathConstraints
from pybatfish.datamodel.answer import TableAnswer
from pybatfish.exception import (
    BatfishAssertException,
    BatfishAssertWarning,
    BatfishException,
)
from pybatfish.question.question import QuestionBase


def test_raise_common_default():
    with pytest.raises(BatfishAssertException) as e:
        _raise_common("foobar")
    assert "foobar" in str(e.value)

    with pytest.raises(BatfishAssertException) as e:
        _raise_common("foobaragain", False)
    assert "foobaragain" in str(e.value)


def test_raise_common_warn():
    with pytest.warns(BatfishAssertWarning):
        result = _raise_common("foobar", True)
    assert not result


def test_format_df_illegal_format():
    with pytest.raises(ValueError):
        _format_df(None, "nothing")


def test_format_df_table():
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    assert _format_df(df, "table") == df.to_string()


def test_format_df_records():
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    assert _format_df(df, "records") == str(df.to_dict(orient="records"))


class MockTableAnswer(TableAnswer):
    def __init__(self, frame_to_use=DataFrame()):
        self._frame = frame_to_use

    def frame(self):
        return self._frame


class MockQuestion(QuestionBase):
    def __init__(self, answer=None):
        self._answer = answer if answer is not None else MockTableAnswer()

    def answer(self, *args, **kwargs):
        return self._answer


def test_filter_denies():
    """Confirm filter-denies assert passes and fails as expected when specifying a session."""
    headers = HeaderConstraints(srcIps="1.1.1.1")
    bf = Session(load_questions=False)
    with patch.object(bf.q, "searchFilters", create=True) as mock_search_filters:
        # Test success
        mock_search_filters.return_value = MockQuestion()
        assert_filter_denies("filter", headers, session=bf)
        mock_search_filters.assert_called_with(
            filters="filter", headers=headers, action="permit"
        )
        # Test failure; also test that startLocation is passed through
        mock_df = DataFrame.from_records([{"Flow": "found", "More": "data"}])
        mock_search_filters.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_filter_denies(
                "filter", headers, startLocation="Ethernet1", session=bf
            )
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        mock_search_filters.assert_called_with(
            filters="filter",
            headers=headers,
            startLocation="Ethernet1",
            action="permit",
        )


def test_filter_denies_from_session():
    """Confirm filter-denies assert passes and fails as expected when called from a session."""
    headers = HeaderConstraints(srcIps="1.1.1.1")
    bf = Session(load_questions=False)
    with patch.object(bf.q, "searchFilters", create=True) as mock_search_filters:
        # Test success
        mock_search_filters.return_value = MockQuestion()
        bf.asserts.assert_filter_denies("filter", headers)
        mock_search_filters.assert_called_with(
            filters="filter", headers=headers, action="permit"
        )
        # Test failure; also test that startLocation is passed through
        mock_df = DataFrame.from_records([{"Flow": "found", "More": "data"}])
        mock_search_filters.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_filter_denies(
                "filter", headers, startLocation="Ethernet1"
            )
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        mock_search_filters.assert_called_with(
            filters="filter",
            headers=headers,
            startLocation="Ethernet1",
            action="permit",
        )


def test_filter_has_no_unreachable_lines():
    """Confirm filter-has-no-unreachable-lines assert passes and fails as expected when specifying a session."""
    filters = "filter1"
    bf = Session(load_questions=False)
    with patch.object(
        bf.q, "filterLineReachability", create=True
    ) as filterLineReachability:
        # Test success
        filterLineReachability.return_value = MockQuestion()
        assert_filter_has_no_unreachable_lines(filters=filters, session=bf)
        # Test failure
        mock_df = DataFrame.from_records([{"UnreachableLine": "found", "More": "data"}])
        filterLineReachability.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_filter_has_no_unreachable_lines(filters=filters, session=bf)
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)


def test_filter_has_no_unreachable_lines_from_session():
    """Confirm filter-has-no-unreachable-lines assert passes and fails as expected when called from a session."""
    filters = "filter1"
    bf = Session(load_questions=False)
    with patch.object(
        bf.q, "filterLineReachability", create=True
    ) as filterLineReachability:
        # Test success
        filterLineReachability.return_value = MockQuestion()
        bf.asserts.assert_filter_has_no_unreachable_lines(filters=filters)
        # Test failure
        mock_df = DataFrame.from_records([{"UnreachableLine": "found", "More": "data"}])
        filterLineReachability.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_filter_has_no_unreachable_lines(filters=filters)
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)


def test_filter_permits():
    """Confirm filter-permits assert passes and fails as expected when specifying a session."""
    headers = HeaderConstraints(srcIps="1.1.1.1")
    bf = Session(load_questions=False)
    with patch.object(bf.q, "searchFilters", create=True) as mock_search_filters:
        # Test success
        mock_search_filters.return_value = MockQuestion()
        assert_filter_permits("filter", headers, session=bf)
        mock_search_filters.assert_called_with(
            filters="filter", headers=headers, action="deny"
        )
        # Test failure; also test that startLocation is passed through
        mock_df = DataFrame.from_records([{"Flow": "found", "More": "data"}])
        mock_search_filters.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_filter_permits(
                "filter", headers, startLocation="Ethernet1", session=bf
            )
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        mock_search_filters.assert_called_with(
            filters="filter", headers=headers, startLocation="Ethernet1", action="deny"
        )


def test_filter_permits_from_session():
    """Confirm filter-permits assert passes and fails as expected when called from a session."""
    headers = HeaderConstraints(srcIps="1.1.1.1")
    bf = Session(load_questions=False)
    with patch.object(bf.q, "searchFilters", create=True) as mock_search_filters:
        # Test success
        mock_search_filters.return_value = MockQuestion()
        bf.asserts.assert_filter_permits("filter", headers)
        mock_search_filters.assert_called_with(
            filters="filter", headers=headers, action="deny"
        )
        # Test failure; also test that startLocation is passed through
        mock_df = DataFrame.from_records([{"Flow": "found", "More": "data"}])
        mock_search_filters.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_filter_permits(
                "filter", headers, startLocation="Ethernet1"
            )
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        mock_search_filters.assert_called_with(
            filters="filter", headers=headers, startLocation="Ethernet1", action="deny"
        )


def test_flows_fail():
    """Confirm flows-fail assert passes and fails as expected when specifying a session."""
    startLocation = "node1"
    headers = HeaderConstraints(srcIps="1.1.1.1")
    bf = Session(load_questions=False)
    with patch.object(bf.q, "reachability", create=True) as reachability:
        # Test success
        reachability.return_value = MockQuestion()
        assert_flows_fail(startLocation, headers, session=bf)
        reachability.assert_called_with(
            pathConstraints=PathConstraints(startLocation=startLocation),
            headers=headers,
            actions="success",
        )
        # Test failure
        mock_df = DataFrame.from_records([{"Flow": "found", "More": "data"}])
        reachability.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_flows_fail(startLocation, headers, session=bf)
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        reachability.assert_called_with(
            pathConstraints=PathConstraints(startLocation=startLocation),
            headers=headers,
            actions="success",
        )


def test_flows_fail_from_session():
    """Confirm flows-fail assert passes and fails as expected when called from a session."""
    startLocation = "node1"
    headers = HeaderConstraints(srcIps="1.1.1.1")
    bf = Session(load_questions=False)
    with patch.object(bf.q, "reachability", create=True) as reachability:
        # Test success
        reachability.return_value = MockQuestion()
        bf.asserts.assert_flows_fail(startLocation, headers)
        reachability.assert_called_with(
            pathConstraints=PathConstraints(startLocation=startLocation),
            headers=headers,
            actions="success",
        )
        # Test failure
        mock_df = DataFrame.from_records([{"Flow": "found", "More": "data"}])
        reachability.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_flows_fail(startLocation, headers)
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        reachability.assert_called_with(
            pathConstraints=PathConstraints(startLocation=startLocation),
            headers=headers,
            actions="success",
        )


def test_flows_succeed():
    """Confirm flows-succeed assert passes and fails as expected when specifying a session."""
    startLocation = "node1"
    headers = HeaderConstraints(srcIps="1.1.1.1")
    bf = Session(load_questions=False)
    with patch.object(bf.q, "reachability", create=True) as reachability:
        # Test success
        reachability.return_value = MockQuestion()
        assert_flows_succeed(startLocation, headers, session=bf)
        reachability.assert_called_with(
            pathConstraints=PathConstraints(startLocation=startLocation),
            headers=headers,
            actions="failure",
        )
        # Test failure
        mock_df = DataFrame.from_records([{"Flow": "found", "More": "data"}])
        reachability.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_flows_succeed(startLocation, headers, session=bf)
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        reachability.assert_called_with(
            pathConstraints=PathConstraints(startLocation=startLocation),
            headers=headers,
            actions="failure",
        )


def test_flows_succeed_from_session():
    """Confirm flows-succeed assert passes and fails as expected when called from a session."""
    startLocation = "node1"
    headers = HeaderConstraints(srcIps="1.1.1.1")
    bf = Session(load_questions=False)
    with patch.object(bf.q, "reachability", create=True) as reachability:
        # Test success
        reachability.return_value = MockQuestion()
        bf.asserts.assert_flows_succeed(startLocation, headers)
        reachability.assert_called_with(
            pathConstraints=PathConstraints(startLocation=startLocation),
            headers=headers,
            actions="failure",
        )
        # Test failure
        mock_df = DataFrame.from_records([{"Flow": "found", "More": "data"}])
        reachability.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_flows_succeed(startLocation, headers)
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        reachability.assert_called_with(
            pathConstraints=PathConstraints(startLocation=startLocation),
            headers=headers,
            actions="failure",
        )


def test_no_incompatible_bgp_sessions():
    """Confirm no-incompatible-bgp-sessions assert passes and fails as expected when specifying a session."""
    bf = Session(load_questions=False)
    with patch.object(
        bf.q, "bgpSessionCompatibility", create=True
    ) as bgpSessionCompatibility:
        # Test success
        bgpSessionCompatibility.return_value = MockQuestion()
        assert_no_incompatible_bgp_sessions(
            nodes="nodes", remote_nodes="remote_nodes", status=".*", session=bf
        )
        bgpSessionCompatibility.assert_called_with(
            nodes="nodes", remoteNodes="remote_nodes", status=".*"
        )
        # Test failure
        mock_df = DataFrame.from_records([{"Session": "found", "More": "data"}])
        bgpSessionCompatibility.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_no_incompatible_bgp_sessions(
                nodes="nodes", remote_nodes="remote_nodes", status=".*", session=bf
            )
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        bgpSessionCompatibility.assert_called_with(
            nodes="nodes", remoteNodes="remote_nodes", status=".*"
        )


def test_no_incompatible_bgp_sessions_from_session():
    """Confirm no-incompatible-bgp-sessions assert passes and fails as expected when called from a session."""
    bf = Session(load_questions=False)
    with patch.object(
        bf.q, "bgpSessionCompatibility", create=True
    ) as bgpSessionCompatibility:
        # Test success
        bgpSessionCompatibility.return_value = MockQuestion()
        bf.asserts.assert_no_incompatible_bgp_sessions(
            nodes="nodes", remote_nodes="remote_nodes", status=".*"
        )
        bgpSessionCompatibility.assert_called_with(
            nodes="nodes", remoteNodes="remote_nodes", status=".*"
        )
        # Test failure
        mock_df = DataFrame.from_records([{"Session": "found", "More": "data"}])
        bgpSessionCompatibility.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_no_incompatible_bgp_sessions(
                nodes="nodes", remote_nodes="remote_nodes", status=".*"
            )
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        bgpSessionCompatibility.assert_called_with(
            nodes="nodes", remoteNodes="remote_nodes", status=".*"
        )


def test_no_incompatible_ospf_sessions():
    """Confirm no-incompatible-ospf-sessions assert passes and fails as expected when specifying a session."""
    bf = Session(load_questions=False)
    with patch.object(
        bf.q, "ospfSessionCompatibility", create=True
    ) as ospfSessionCompatibility:
        # Test success
        ospfSessionCompatibility.return_value = MockQuestion()
        assert_no_incompatible_ospf_sessions(
            nodes="nodes", remote_nodes="remote_nodes", session=bf
        )
        ospfSessionCompatibility.assert_called_with(
            nodes="nodes",
            remoteNodes="remote_nodes",
            statuses=UNESTABLISHED_OSPF_SESSION_STATUS_SPEC,
        )
        # Test failure
        mock_df = DataFrame.from_records([{"Session": "found", "More": "data"}])
        ospfSessionCompatibility.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_no_incompatible_ospf_sessions(
                nodes="nodes", remote_nodes="remote_nodes", session=bf
            )
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        ospfSessionCompatibility.assert_called_with(
            nodes="nodes",
            remoteNodes="remote_nodes",
            statuses=UNESTABLISHED_OSPF_SESSION_STATUS_SPEC,
        )


def test_no_incompatible_ospf_sessions_from_session():
    """Confirm no-incompatible-ospf-sessions assert passes and fails as expected when called from a session."""
    bf = Session(load_questions=False)
    with patch.object(
        bf.q, "ospfSessionCompatibility", create=True
    ) as ospfSessionCompatibility:
        # Test success
        ospfSessionCompatibility.return_value = MockQuestion()
        bf.asserts.assert_no_incompatible_ospf_sessions(
            nodes="nodes", remote_nodes="remote_nodes"
        )
        ospfSessionCompatibility.assert_called_with(
            nodes="nodes",
            remoteNodes="remote_nodes",
            statuses=UNESTABLISHED_OSPF_SESSION_STATUS_SPEC,
        )
        # Test failure
        mock_df = DataFrame.from_records([{"Session": "found", "More": "data"}])
        ospfSessionCompatibility.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_no_incompatible_ospf_sessions(
                nodes="nodes", remote_nodes="remote_nodes"
            )
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        ospfSessionCompatibility.assert_called_with(
            nodes="nodes",
            remoteNodes="remote_nodes",
            statuses=UNESTABLISHED_OSPF_SESSION_STATUS_SPEC,
        )


def test_no_unestablished_bgp_sessions():
    """Confirm no-uncompatible-bgp-sessions assert passes and fails as expected when specifying a session."""
    bf = Session(load_questions=False)
    with patch.object(bf.q, "bgpSessionStatus", create=True) as bgpSessionStatus:
        # Test success
        bgpSessionStatus.return_value = MockQuestion()
        assert_no_unestablished_bgp_sessions(
            nodes="nodes", remote_nodes="remote_nodes", session=bf
        )
        bgpSessionStatus.assert_called_with(
            nodes="nodes", remoteNodes="remote_nodes", status="NOT_ESTABLISHED"
        )
        # Test failure
        mock_df = DataFrame.from_records([{"Session": "found", "More": "data"}])
        bgpSessionStatus.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_no_unestablished_bgp_sessions(
                nodes="nodes", remote_nodes="remote_nodes", session=bf
            )
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        bgpSessionStatus.assert_called_with(
            nodes="nodes", remoteNodes="remote_nodes", status="NOT_ESTABLISHED"
        )


def test_no_unestablished_bgp_sessions_from_session():
    """Confirm no-uncompatible-bgp-sessions assert passes and fails as expected when called from a session."""
    bf = Session(load_questions=False)
    with patch.object(bf.q, "bgpSessionStatus", create=True) as bgpSessionStatus:
        # Test success
        bgpSessionStatus.return_value = MockQuestion()
        bf.asserts.assert_no_unestablished_bgp_sessions(
            nodes="nodes", remote_nodes="remote_nodes"
        )
        bgpSessionStatus.assert_called_with(
            nodes="nodes", remoteNodes="remote_nodes", status="NOT_ESTABLISHED"
        )
        # Test failure
        mock_df = DataFrame.from_records([{"Session": "found", "More": "data"}])
        bgpSessionStatus.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_no_unestablished_bgp_sessions(
                nodes="nodes", remote_nodes="remote_nodes"
            )
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        bgpSessionStatus.assert_called_with(
            nodes="nodes", remoteNodes="remote_nodes", status="NOT_ESTABLISHED"
        )


def test_no_undefined_references():
    """Confirm no-undefined-references assert passes and fails as expected when specifying a session."""
    bf = Session(load_questions=False)
    with patch.object(bf.q, "undefinedReferences", create=True) as undefinedReferences:
        # Test success
        undefinedReferences.return_value = MockQuestion()
        assert_no_undefined_references(session=bf)
        # Test failure
        mock_df = DataFrame.from_records([{"UndefRef": "found", "More": "data"}])
        undefinedReferences.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_no_undefined_references(session=bf)
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)


def test_no_undefined_references_from_session():
    """Confirm no-undefined-references assert passes and fails as expected when called from a session."""
    bf = Session(load_questions=False)
    with patch.object(bf.q, "undefinedReferences", create=True) as undefinedReferences:
        # Test success
        undefinedReferences.return_value = MockQuestion()
        bf.asserts.assert_no_undefined_references()
        # Test failure
        mock_df = DataFrame.from_records([{"UndefRef": "found", "More": "data"}])
        undefinedReferences.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_no_undefined_references()
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)


def test_no_duplicate_router_ids_ospf():
    """Confirm no-duplicate-router-ids assert passes and fails as expected when specifying a session."""
    bf = Session(load_questions=False)
    with patch.object(
        bf.q, "ospfProcessConfiguration", create=True
    ) as ospfProcessConfiguration:
        # Test success
        mock_df_unique = DataFrame.from_records(
            [
                {"Router_ID": "1.1.1.1", "VRF": "vrf1"},
                {"Router_ID": "1.1.1.2", "VRF": "vrf2"},
            ]
        )
        ospfProcessConfiguration.return_value = MockQuestion(
            MockTableAnswer(mock_df_unique)
        )
        assert_no_duplicate_router_ids(session=bf, protocols=["ospf"])
        # Test failure
        mock_df_duplicate = DataFrame.from_records(
            [
                {"Router_ID": "1.1.1.1", "VRF": "vrf1"},
                {"Router_ID": "1.1.1.1", "VRF": "vrf2"},
            ]
        )
        ospfProcessConfiguration.return_value = MockQuestion(
            MockTableAnswer(mock_df_duplicate)
        )
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_no_duplicate_router_ids(session=bf, protocols=["ospf"])
        # Ensure found answer is printed
        assert mock_df_duplicate.to_string() in str(excinfo.value)


def test_no_duplicate_router_ids_bgp():
    """Confirm no-duplicate-router-ids assert passes and fails as expected when specifying a session."""
    bf = Session(load_questions=False)
    with patch.object(
        bf.q, "bgpProcessConfiguration", create=True
    ) as bgpProcessConfiguration:
        # Test success
        mock_df_unique = DataFrame.from_records(
            [
                {"Router_ID": "1.1.1.1", "VRF": "vrf1"},
                {"Router_ID": "1.1.1.2", "VRF": "vrf2"},
            ]
        )
        bgpProcessConfiguration.return_value = MockQuestion(
            MockTableAnswer(mock_df_unique)
        )
        assert_no_duplicate_router_ids(session=bf, protocols=["bgp"])
        # Test failure
        mock_df_duplicate = DataFrame.from_records(
            [
                {"Router_ID": "1.1.1.1", "VRF": "vrf1"},
                {"Router_ID": "1.1.1.1", "VRF": "vrf2"},
            ]
        )
        bgpProcessConfiguration.return_value = MockQuestion(
            MockTableAnswer(mock_df_duplicate)
        )
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_no_duplicate_router_ids(session=bf, protocols=["bgp"])
        # Ensure found answer is printed
        assert mock_df_duplicate.to_string() in str(excinfo.value)


def test_no_duplicate_router_ids_from_session():
    """Confirm no-duplicate-router-ids assert passes and fails as expected when called from a session."""
    bf = Session(load_questions=False)
    with patch.object(
        bf.q, "bgpProcessConfiguration", create=True
    ) as bgpProcessConfiguration:
        # Test success
        mock_df_unique = DataFrame.from_records(
            [
                {"Router_ID": "1.1.1.1", "VRF": "vrf1"},
                {"Router_ID": "1.1.1.2", "VRF": "vrf2"},
            ]
        )
        bgpProcessConfiguration.return_value = MockQuestion(
            MockTableAnswer(mock_df_unique)
        )
        bf.asserts.assert_no_duplicate_router_ids(protocols=["bgp"])
        # Test failure
        mock_df_duplicate = DataFrame.from_records(
            [
                {"Router_ID": "1.1.1.1", "VRF": "vrf1"},
                {"Router_ID": "1.1.1.1", "VRF": "vrf2"},
            ]
        )
        bgpProcessConfiguration.return_value = MockQuestion(
            MockTableAnswer(mock_df_duplicate)
        )
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_no_duplicate_router_ids(protocols=["bgp"])
        # Ensure found answer is printed
        assert mock_df_duplicate.to_string() in str(excinfo.value)


def test_no_forwarding_loops():
    """Confirm no-forwarding-loops assert passes and fails as expected when specifying a session."""
    bf = Session(load_questions=False)
    with patch.object(bf.q, "detectLoops", create=True) as detectLoops:
        # Test success
        detectLoops.return_value = MockQuestion()
        assert_no_forwarding_loops(session=bf)
        # Test failure
        mock_df = DataFrame.from_records([{"Loop": "found", "More": "data"}])
        detectLoops.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_no_forwarding_loops(session=bf)
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)


def test_no_forwarding_loops_from_session():
    """Confirm no-forwarding-loops assert passes and fails as expected when called from a session."""
    bf = Session(load_questions=False)
    with patch.object(bf.q, "detectLoops", create=True) as detectLoops:
        # Test success
        detectLoops.return_value = MockQuestion()
        bf.asserts.assert_no_forwarding_loops()
        # Test failure
        mock_df = DataFrame.from_records([{"Loop": "found", "More": "data"}])
        detectLoops.return_value = MockQuestion(MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            bf.asserts.assert_no_forwarding_loops()
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)


def test_get_question_object():
    """Confirm _get_question_object identifies the correct question object based on the specified session and the questions it contains."""
    # Session contains the question we're searching for
    bf = Session(load_questions=False)
    with patch.object(bf.q, "qName", create=True):
        assert bf.q == _get_question_object(bf, "qName")

    # Cannot find the question we're searching for
    with pytest.raises(BatfishException) as err:
        _get_question_object(bf, "qMissing")
    assert "qMissing question was not found" in str(err.value)


def test_is_dict_match():
    # equal
    assert _is_dict_match({"k1": "v1", "k2": "v2"}, {"k1": "v1", "k2": "v2"})

    # strict subset
    assert _is_dict_match({"k1": "v1", "k2": "v2"}, {"k1": "v1"})

    # extra key
    assert not _is_dict_match({"k1": "v1", "k2": "v2"}, {"k3": "v3"})

    # wrong value
    assert not _is_dict_match({"k1": "v1", "k2": "v2"}, {"k1": "v3"})


def test_has_route_unsupported_type_routes():
    with pytest.raises(TypeError) as excinfo:
        # noinspection PyTypeChecker
        assert_has_route("bad type", {}, "n1")
    assert "'routes' is neither a Pandas DataFrame nor a dictionary" in str(
        excinfo.value
    )


def test_has_route_dataframe_routes():
    routes = DataFrame(
        {
            "Node": ["n1", "n1"],
            "VRF": ["vrf1", "vrf2"],
            "Network": ["10.10.10.0/24", "20.20.20.0/24"],
        }
    )

    # missing node
    with pytest.raises(BatfishAssertException) as excinfo:
        assert_has_route(routes, {}, "missing_node")
    assert "No node" in str(excinfo.value)

    # missing VRF
    with pytest.raises(BatfishAssertException) as excinfo:
        assert_has_route(routes, {}, "n1", "missing_vrf")
    assert "No VRF" in str(excinfo.value)

    # missing route case 1: network does not exist at all
    with pytest.raises(BatfishAssertException) as excinfo:
        assert_has_route(routes, {"Network": "30.30.30.30/32"}, "n1", "vrf1")
    assert "No route" in str(excinfo.value)

    # missing route case 2: network exists in the wrong vrf
    with pytest.raises(BatfishAssertException) as excinfo:
        assert_has_route(routes, {"Network": "10.10.10.0/24"}, "n1", "vrf2")
    assert "No route" in str(excinfo.value)

    # valid route
    assert_has_route(routes, {"Network": "10.10.10.0/24"}, "n1", "vrf1")


def test_has_route_dict_routes():
    routes = {
        "n1": {
            "vrf1": [{"Network": "10.10.10.0/24"}],
            "vrf2": [{"Network": "20.20.20.0/24"}],
        }
    }

    # missing node
    with pytest.raises(BatfishAssertException) as excinfo:
        assert_has_route(routes, {}, "missing_node")
    assert "No node" in str(excinfo.value)

    # missing VRF
    with pytest.raises(BatfishAssertException) as excinfo:
        assert_has_route(routes, {}, "n1", "missing_vrf")
    assert "No VRF" in str(excinfo.value)

    # missing route case 1: network does not exist at all
    with pytest.raises(BatfishAssertException) as excinfo:
        assert_has_route(routes, {"Network": "30.30.30.30/32"}, "n1", "vrf1")
    assert "No route" in str(excinfo.value)

    # missing route case 2: network exists in the wrong vrf
    with pytest.raises(BatfishAssertException) as excinfo:
        assert_has_route(routes, {"Network": "10.10.10.0/24"}, "n1", "vrf2")
    assert "No route" in str(excinfo.value)

    # valid route
    assert_has_route(routes, {"Network": "10.10.10.0/24"}, "n1", "vrf1")


def test_has_no_route_unsupported_type_routes():
    with pytest.raises(TypeError) as excinfo:
        # noinspection PyTypeChecker
        assert_has_no_route("bad type", {}, "n1")
    assert "'routes' is neither a Pandas DataFrame nor a dictionary" in str(
        excinfo.value
    )


def test_has_no_route_dataframe_routes():
    routes = DataFrame(
        {
            "Node": ["n1", "n1"],
            "VRF": ["vrf1", "vrf2"],
            "Network": ["10.10.10.0/24", "20.20.20.0/24"],
        }
    )

    # missing node
    with pytest.warns(BatfishAssertWarning):
        assert_has_no_route(routes, {}, "missing_node")

    # missing VRF
    with pytest.warns(BatfishAssertWarning):
        assert_has_no_route(routes, {}, "n1", "missing_vrf")

    # missing route case 1: network does not exist at all
    assert_has_no_route(routes, {"Network": "30.30.30.30/32"}, "n1", "vrf1")

    # missing route case 2: network exists in the wrong vrf
    assert_has_no_route(routes, {"Network": "10.10.10.0/24"}, "n1", "vrf2")

    # present route
    with pytest.raises(BatfishAssertException) as excinfo:
        assert_has_no_route(routes, {"Network": "10.10.10.0/24"}, "n1", "vrf1")
    assert "Found route(s)" in str(excinfo.value)


def test_has_no_route_dict_routes():
    routes = {
        "n1": {
            "vrf1": [{"Network": "10.10.10.0/24"}],
            "vrf2": [{"Network": "20.20.20.0/24"}],
        }
    }

    # missing node
    with pytest.warns(BatfishAssertWarning):
        assert_has_no_route(routes, {}, "missing_node")

    # missing VRF
    with pytest.warns(BatfishAssertWarning):
        assert_has_no_route(routes, {}, "n1", "missing_vrf")

    # missing route case 1: network does not exist at all
    assert_has_no_route(routes, {"Network": "30.30.30.30/32"}, "n1", "vrf1")

    # missing route case 2: network exists in the wrong vrf
    assert_has_no_route(routes, {"Network": "10.10.10.0/24"}, "n1", "vrf2")

    # present route
    with pytest.raises(BatfishAssertException) as excinfo:
        assert_has_no_route(routes, {"Network": "10.10.10.0/24"}, "n1", "vrf1")
    assert "Found route(s)" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main()
