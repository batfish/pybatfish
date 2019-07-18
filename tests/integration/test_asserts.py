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
from os.path import abspath, dirname, join, realpath

import pytest

from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints

_this_dir = abspath(dirname(realpath(__file__)))


# Just use a single session for all assertion tests
@pytest.fixture(scope='module')
def session():
    s = Session()
    name = s.init_snapshot(join(_this_dir, 'snapshots', 'asserts'))
    yield s
    s.delete_snapshot(name)


@pytest.mark.parametrize('assert_func, params', [
    ('assert_filter_denies',
     {
         'filters': '/101/',
         'headers': HeaderConstraints(srcIps='12.34.56.78'),
         'startLocation': '@enter(node[GigabitEthernet1/0])',
     }
     ),
    ('assert_filter_has_no_unreachable_lines',
     {
         'filters': '/101/',
     }
     ),
    ('assert_filter_permits',
     {
         'filters': '/101/',
         'headers': HeaderConstraints(srcIps='1.0.1.0', dstIps='8.8.8.8'),
         'startLocation': '@enter(node[GigabitEthernet1/0])',
     }
     ),
    ('assert_flows_fail',
     {
         'startLocation': '@enter(node[GigabitEthernet1/0])',
         'headers': HeaderConstraints(srcIps='12.34.56.78', dstIps='1.0.1.0',
                                      ipProtocols=['TCP']),
     }
     ),
    ('assert_flows_succeed',
     {
         'startLocation': '@enter(node[GigabitEthernet1/0])',
         'headers': HeaderConstraints(srcIps='2.0.1.0', dstIps='1.0.1.0',
                                      ipProtocols=['TCP']),
     }
     ),
    ('assert_no_incompatible_bgp_sessions',
     {}
     ),
    ('assert_no_unestablished_bgp_sessions',
     {}
     ),
    ('assert_no_undefined_references',
     {}
     ),
])
def test_asserts_run(session, assert_func, params):
    """Test that each assertion runs successfully."""
    # Assertion should run without errors and return True (passing assert)
    assert getattr(session.asserts, assert_func)(**params)
