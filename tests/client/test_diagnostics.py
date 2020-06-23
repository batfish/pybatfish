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
import tempfile
import uuid

import pytest
import responses
from requests import HTTPError

from pybatfish.client._diagnostics import (
    METADATA_FILENAME,
    _UPLOAD_MAX_TRIES,
    _anonymize_dir,
    _upload_dir_to_url,
    check_if_all_passed,
    check_if_any_failed,
    upload_diagnostics,
)
from pybatfish.client.session import Session

# Config file constants for anonymization and upload
_CONFIG_IP_ADDR = "1.2.3.4"
_CONFIG_PASSWORD = "myPassword"
_CONFIG_FILE = "file.cfg"
_CONFIG_CONTENT = "username blah password {password}\nsomething {ip}\n".format(
    password=_CONFIG_PASSWORD, ip=_CONFIG_IP_ADDR
)


@pytest.fixture()
def config_dir(tmpdir):
    dir_path = str(tmpdir.mkdir("config"))
    with open(os.path.join(dir_path, _CONFIG_FILE), "w") as f:
        f.write(_CONFIG_CONTENT)
        f.flush()
        yield dir_path


def test_anonymize(config_dir, tmpdir):
    """Confirm default anonymization removes password and IP address."""
    _anonymize_dir(config_dir, str(tmpdir))

    # Confirm the password is anonymized but IP address is left alone, per anonymization config
    with open(os.path.join(str(tmpdir), _CONFIG_FILE), "r") as f:
        anon_text = f.read()
        assert _CONFIG_PASSWORD not in anon_text
        assert _CONFIG_IP_ADDR not in anon_text


def test_anonymize_custom(config_dir, tmpdir):
    """Confirm custom anonymization removes only what is specified in config."""
    # Generate Netconan config which will anonymize passwords but NOT IP addresses
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write("anonymize-passwords\n")
        f.seek(0)
        _anonymize_dir(config_dir, str(tmpdir), netconan_config=f.name)

    # Confirm the password is anonymized but IP address is left alone, per anonymization config
    with open(os.path.join(str(tmpdir), _CONFIG_FILE), "r") as f:
        anon_text = f.read()
        assert _CONFIG_PASSWORD not in anon_text
        assert _CONFIG_IP_ADDR in anon_text


def test_check_if_snapshot_passed():
    """Test checking init info statuses for PASSED status."""
    # Confirm result is True iff all values are PASSED
    assert check_if_all_passed({"a": "PASSED", "b": "PASSED"})
    assert not check_if_all_passed({"a": "PASSED", "b": "FAILED"})
    assert not check_if_all_passed({"a": "PASSED", "b": "WARNINGS"})
    assert not check_if_all_passed({"a": "FAILED", "b": "FAILED"})


def test_check_if_snapshot_failed():
    """Test checking init info statuses for FAILED status."""
    # Confirm result is False iff at least one value is FAILED
    assert not check_if_any_failed({"a": "PASSED", "b": "PASSED"})
    assert not check_if_any_failed({"a": "PASSED", "b": "EMPTY"})
    assert check_if_any_failed({"a": "PASSED", "b": "FAILED"})
    assert check_if_any_failed({"a": "FAILED", "b": "FAILED"})


def test_upload_diagnostics_metadata():
    """Confirm metadata file is generated with correct content."""
    metadata = {"test_key1": "test_value", "test_key2": 1234}
    out_dir = upload_diagnostics(
        Session(load_questions=False), metadata, dry_run=True, questions=[]
    )

    with open(os.path.join(out_dir, METADATA_FILENAME)) as f:
        contents = json.loads(f.read())

    assert contents == metadata


@responses.activate
def test_upload_to_url(config_dir):
    """Confirm config file is uploaded to a fake S3 bucket."""
    dir_name = uuid.uuid4().hex
    base_url = "https://{bucket}.s3-{region}.amazonaws.com/{resource}".format(
        bucket="bucket", region="region", resource=dir_name
    )
    resource_url = "{}/{}".format(base_url, _CONFIG_FILE)
    uploads = {}

    def put_callback(request):
        uploads[request.url] = request.body.read().decode("utf-8")
        return 200, {}, json.dumps({})

    # Intercept the PUT request destined for the S3 bucket, and just add file contents to uploads dict
    responses.add_callback(responses.PUT, resource_url, callback=put_callback)

    _upload_dir_to_url(base_url=base_url, src_dir=config_dir)

    # Make sure the entry populated by the put request matches the original file contents
    assert uploads[resource_url] == _CONFIG_CONTENT


@responses.activate
def test_upload_to_url_retry(config_dir):
    """Confirm we retry uploading if it fails at first."""
    dir_name = uuid.uuid4().hex
    base_url = "https://{bucket}.s3-{region}.amazonaws.com/{resource}".format(
        bucket="bucket", region="region", resource=dir_name
    )
    resource_url = "{}/{}".format(base_url, _CONFIG_FILE)

    # Unsuccessful mock put result
    responses.add(responses.PUT, resource_url, json={"error": "conn reset"}, status=104)

    # Eventually we should give up and throw an HTTPError
    with pytest.raises(HTTPError):
        _upload_dir_to_url(base_url=base_url, src_dir=config_dir)

    # Should have tried to upload a few times
    assert len(responses.calls) == _UPLOAD_MAX_TRIES
