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
"""Integration tests of pybatfish using Batfish service.

This test file operates over the example test rigs in the batfish repository.
It assumes that it runs from the top-level directory in the repository.

To get relevant shell commands, do:
`source tools/batfish_function.sh`

The client runs against the batfish service, hosted locally or on a remote server.
To start the service locally, do the following in a new shell:
`source tools/batfish_functions.sh`
`allinone -runmode interactive`
"""

from __future__ import absolute_import, print_function

from os.path import abspath, join, realpath, pardir, dirname

import pytest

from pybatfish.client.commands import (bf_generate_dataplane,
                                       bf_init_snapshot,
                                       bf_delete_network, bf_session,
                                       bf_init_network)
from pybatfish.client.consts import BfConsts
from pybatfish.question.question import load_questions

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))
_test_rig_dir = join(_root_dir, 'test_rigs')
TEST_NETWORK = 'ref_network'


@pytest.fixture(scope='module')
def questions():
    load_questions()

    bf_session.additionalArgs[BfConsts.ARG_VERBOSE_PARSE] = True
    bf_session.additionalArgs[BfConsts.ARG_HALT_ON_CONVERT_ERROR] = True
    bf_session.additionalArgs[BfConsts.ARG_HALT_ON_PARSE_ERROR] = True

    try:
        bf_delete_network(TEST_NETWORK)
    except Exception:
        pass
    yield bf_init_network(TEST_NETWORK)
    bf_delete_network(TEST_NETWORK)


def test_e2e(questions):
    """Run a series of commands against Batfish. The goal is not to crash."""
    bf_init_snapshot(join(_test_rig_dir, 'example'))
    bf_init_snapshot(join(_test_rig_dir, 'example-with-delta'), 'example-with-delta')
    bf_generate_dataplane()
    bf_generate_dataplane('example-with-delta')
