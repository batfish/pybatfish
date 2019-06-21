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

from pybatfish.client._facts import load_facts
from pybatfish.client.session import Session

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))


@pytest.fixture()
def session():
    s = Session()
    name = s.init_snapshot(join(_this_dir, 'facts', 'fact_snapshot'))
    yield s
    s.delete_snapshot(name)


def test_extract_facts(tmpdir, session):
    """Test extraction of facts for the current snapshot with a basic config."""
    out_dir = tmpdir.join('output')
    extracted_facts = session.extract_facts(nodes='basic',
                                            output_directory=str(out_dir))

    written_facts = load_facts(str(out_dir))
    expected_facts = load_facts(join(_this_dir, 'facts', 'expected_facts'))

    assert extracted_facts == expected_facts, 'Extracted facts match expected facts'
    assert written_facts == expected_facts, 'Facts written to disk match expected facts'


def test_validate_facts_matching(session):
    """Test validation of facts for the current snapshot against matching facts."""
    validation_results = session.validate_facts(
        expected_facts=join(_this_dir, 'facts', 'expected_facts'),
        nodes='basic')

    assert validation_results == {}, 'No differences between expected and actual facts'


def test_validate_facts_different(session):
    """Test validation of facts for the current snapshot against different facts."""
    validation_results = session.validate_facts(
        expected_facts=join(_this_dir, 'facts', 'unexpected_facts'),
        nodes='basic')

    assert validation_results == {
        'basic': {
            'DNS.DNS_Servers': {
                'actual': [],
                'expected': ['1.2.3.4'],
            },
        }
    }, 'Only DNS servers should be different between expected and actual facts'
