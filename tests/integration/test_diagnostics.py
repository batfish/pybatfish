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
import uuid
from os.path import abspath, dirname, join, pardir, realpath

import pytest
import requests

from pybatfish.client._diagnostics import (_INIT_INFO_QUESTIONS, _S3_BUCKET,
                                           _S3_REGION, upload_diagnostics)
from pybatfish.client.commands import (bf_delete_network,
                                       bf_delete_snapshot, bf_init_snapshot,
                                       bf_session, bf_set_network)
from pybatfish.question.question import QuestionBase

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))


@pytest.fixture()
def network():
    name = bf_set_network()
    yield name
    # cleanup
    bf_delete_network(name)


@pytest.fixture()
def example_snapshot(network):
    bf_set_network(network)
    name = uuid.uuid4().hex
    bf_init_snapshot(join(_this_dir, 'snapshot'), name)
    yield name
    # cleanup
    bf_delete_snapshot(name)


def test_questions(network, example_snapshot):
    """Run diagnostic questions on example snapshot."""
    for template in _INIT_INFO_QUESTIONS:
        # Goal here is to run question successfully, i.e. not crash
        QuestionBase(template, bf_session).answer()


def test_upload_diagnostics(network, example_snapshot):
    """Upload initialization information for example snapshot."""
    # This call raises an exception if any file upload results in HTTP status != 200
    resource = upload_diagnostics(session=bf_session, metadata={},
                                  dry_run=False, resource_prefix='test/')
    base_url = 'https://{bucket}.s3-{region}.amazonaws.com'.format(
        bucket=_S3_BUCKET, region=_S3_REGION)

    # Confirm none of the uploaded questions are accessible
    for template in _INIT_INFO_QUESTIONS:
        q = QuestionBase(template, bf_session)
        r = requests.get('{}/{}/{}'.format(base_url, resource, q.get_name()))
        assert (r.status_code == 403)
