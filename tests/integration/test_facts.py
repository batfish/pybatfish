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
from os.path import abspath, dirname, join, pardir, realpath

import pytest

from pybatfish.client._facts import load_facts, validate_facts
from pybatfish.client.session import Session
from tests.common_util import requires_bf

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))

_CURRENT_SNAPSHOT = "current_snapshot"
_PREVIOUS_SNAPSHOT = "previous_snapshot"


@pytest.fixture(scope="module")
def session():
    s = Session()
    # Snapshot which can be referenced by name
    other_name = s.init_snapshot(
        join(_this_dir, "snapshots", "fact_snapshot2"), _PREVIOUS_SNAPSHOT
    )
    # Current snapshot
    name = s.init_snapshot(
        join(_this_dir, "snapshots", "fact_snapshot"), _CURRENT_SNAPSHOT
    )
    yield s
    s.delete_snapshot(name)
    s.delete_snapshot(other_name)


@requires_bf("2022.01.20")
def test_extract_facts(tmpdir, session):
    """Test extraction of facts for the current snapshot with a basic config."""
    out_dir = tmpdir.join("output")
    extracted_facts = session.extract_facts(
        nodes="basic", output_directory=str(out_dir)
    )

    written_facts = load_facts(str(out_dir))
    expected_facts = load_facts(join(_this_dir, "facts", "expected_facts"))

    assert (
        validate_facts(expected_facts, extracted_facts) == {}
    ), "Extracted facts match expected facts"
    assert (
        validate_facts(expected_facts, written_facts) == {}
    ), "Written facts match expected facts"


def test_extract_facts_specific_snapshot(tmpdir, session):
    """Test extraction of facts for a specific snapshot."""
    out_dir = tmpdir.join("output")
    extracted_facts = session.extract_facts(
        output_directory=str(out_dir), snapshot=_PREVIOUS_SNAPSHOT
    )

    written_facts = load_facts(str(out_dir))
    expected_facts = load_facts(join(_this_dir, "facts", "expected_facts2"))

    assert (
        validate_facts(expected_facts, extracted_facts) == {}
    ), "Extracted facts match expected facts"
    assert (
        validate_facts(expected_facts, written_facts) == {}
    ), "Written facts match expected facts"


@requires_bf("2022.01.20")
def test_validate_facts_matching(session):
    """Test validation of facts for the current snapshot against matching facts."""
    validation_results = session.validate_facts(
        expected_facts=join(_this_dir, "facts", "expected_facts")
    )

    assert validation_results == {}, "No differences between expected and actual facts"


def test_validate_facts_matching_specific_snapshot(session):
    """Test validation of facts against matching facts, for a specific snapshot."""
    validation_results = session.validate_facts(
        expected_facts=join(_this_dir, "facts", "expected_facts2"),
        snapshot=_PREVIOUS_SNAPSHOT,
    )

    assert validation_results == {}, "No differences between expected and actual facts"


def test_validate_facts_different(session):
    """Test validation of facts for the current snapshot against different facts."""
    validation_results = session.validate_facts(
        expected_facts=join(_this_dir, "facts", "unexpected_facts")
    )

    assert validation_results == {
        "basic": {"DNS.DNS_Servers": {"actual": [], "expected": ["1.2.3.4"]}}
    }, "Only DNS servers should be different between expected and actual facts"
