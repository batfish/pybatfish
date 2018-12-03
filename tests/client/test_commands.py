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
import json
import os
import shutil
import tempfile
import uuid

import pytest
import responses

from pybatfish.client.commands import _generate_s3_url, \
    _anonymize_dir, _upload_dir_to_url
from pybatfish.client.commands import (bf_fork_snapshot, bf_init_snapshot,
                                       bf_set_network)

# Config file constants for anonymization and upload
_CONFIG_IP_ADDR = "1.2.3.4"
_CONFIG_PASSWORD = "myPassword"
_CONFIG_FILE = "file.cfg"
_CONFIG_CONTENT = "username blah password {password}\nsomething {ip}\n".format(
    password=_CONFIG_PASSWORD, ip=_CONFIG_IP_ADDR)

_S3_BUCKET = "bucket-name"
_S3_REGION = "region"


@pytest.fixture()
def config_dir():
    tmp_dir = tempfile.mkdtemp()

    with open(os.path.join(tmp_dir, _CONFIG_FILE), 'w') as f:
        f.write(_CONFIG_CONTENT)
        f.seek(0)
        yield tmp_dir

    shutil.rmtree(tmp_dir)


@pytest.fixture()
def tmp_dir():
    dir_path = tempfile.mkdtemp()
    yield dir_path

    shutil.rmtree(dir_path)


def test_anonymize(config_dir, tmp_dir):
    """Confirm default anonymization removes password and IP address."""
    _anonymize_dir(config_dir, tmp_dir)

    # Confirm the password is anonymized but IP address is left alone, per anonymization config
    with open(os.path.join(tmp_dir, _CONFIG_FILE), 'r') as f:
        anon_text = f.read()
        assert (_CONFIG_PASSWORD not in anon_text)
        assert (_CONFIG_IP_ADDR not in anon_text)


def test_anonymize_custom(config_dir, tmp_dir):
    """Confirm custom anonymization removes only what is specified in config."""

    # Generate Netconan config which will anonymize passwords but NOT IP addresses
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write("anonymize-passwords\n")
        f.seek(0)
        _anonymize_dir(config_dir, tmp_dir,
                       netconan_config=f.name)

    # Confirm the password is anonymized but IP address is left alone, per anonymization config
    with open(os.path.join(tmp_dir, _CONFIG_FILE), 'r') as f:
        anon_text = f.read()
        assert (_CONFIG_PASSWORD not in anon_text)
        assert (_CONFIG_IP_ADDR in anon_text)


def test_network_validation():
    with pytest.raises(ValueError):
        bf_set_network('foo/bar')


def test_snapshot_validation():
    with pytest.raises(ValueError):
        bf_init_snapshot("x", name="foo/bar")


def test_fork_snapshot_validation():
    with pytest.raises(ValueError):
        bf_fork_snapshot(base_name="x", name="foo/bar")


@responses.activate
def test_upload_to_url(config_dir):
    """Confirm config file is uploaded to a fake S3 bucket."""
    dir_name = uuid.uuid4().hex
    base_url = _generate_s3_url(_S3_BUCKET, region=_S3_REGION,
                                resource=dir_name)
    resource_url = '{}/{}'.format(base_url, _CONFIG_FILE)
    uploads = {}

    def put_callback(request):
        uploads[request.url] = request.body.read().decode("utf-8")
        return 200, {}, json.dumps({})

    # Intercept the PUT request destined for the S3 bucket, and just add file contents to uploads dict
    responses.add_callback(
        responses.PUT, resource_url,
        callback=put_callback,
    )

    _upload_dir_to_url(base_url=base_url, src_dir=config_dir)

    # Make sure the entry populated by the put request matches the original file contents
    assert (uploads[resource_url] == _CONFIG_CONTENT)
