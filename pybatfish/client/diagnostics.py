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
"""Contains diagnostic collection and processing functions."""
import json
import logging
import os
import shutil
import tempfile
import uuid
from hashlib import md5
from typing import Dict, Iterable, Optional  # noqa: F401

import requests
from netconan import netconan
from requests import HTTPError

from pybatfish.exception import BatfishException
from pybatfish.question.question import QuestionBase

_CONVERSION_WARNINGS_QUESTION = QuestionBase({
    "class": "org.batfish.question.initialization.ConversionWarningQuestion",
    "differential": False,
    "instance": {
        "instanceName": "__viConversionWarning",
    }
})
_FILE_PARSE_STATUS_QUESTION = QuestionBase({
    "class": "org.batfish.question.initialization.FileParseStatusQuestion",
    "differential": False,
    "instance": {
        "instanceName": "__fileParseStatus",
    }
})
_INIT_INFO_QUESTION = QuestionBase({
    "class": "org.batfish.question.InitInfoQuestionPlugin$InitInfoQuestion",
    "differential": False,
    "instance": {
        "instanceName": "__initInfo"
    },
})
_PARSE_WARNINGS_QUESTION = QuestionBase({
    "class": "org.batfish.question.initialization.ParseWarningQuestion",
    "differential": False,
    "instance": {
        "instanceName": "__parseWarning",
    }
})

# Note: this is a Tuple to enforce immutability.
_INIT_INFO_QUESTIONS = (
    _INIT_INFO_QUESTION,
    _PARSE_WARNINGS_QUESTION,
    _FILE_PARSE_STATUS_QUESTION,
    _CONVERSION_WARNINGS_QUESTION,
)

_S3_BUCKET = 'batfish-diagnostics'
_S3_REGION = 'us-west-2'

bf_logger = logging.getLogger("pybatfish.client")


def _upload_diagnostics(bucket=_S3_BUCKET, region=_S3_REGION, dry_run=True,
                        netconan_config=None, questions=_INIT_INFO_QUESTIONS):
    # type: (str, str, bool, Optional[str], Iterable[QuestionBase]) -> str
    """
    Fetch, anonymize, and optionally upload snapshot initialization information.

    :param bucket: name of the AWS S3 bucket to upload to
    :type bucket: string
    :param region: name of the region containing the bucket
    :type region: string
    :param dry_run: whether or not to skip upload; if False, anonymized files will be stored locally, otherwise anonymized files will be uploaded to the specified S3 bucket
    :type dry_run: bool
    :param netconan_config: path to Netconan configuration file
    :type netconan_config: string
    :param questions: list of questions to run and upload
    :type questions: list[QuestionBase]
    :return: location of anonymized files (local directory if doing dry run, otherwise upload ID)
    :rtype: string
    """
    from pybatfish.client.commands import bf_session

    tmp_dir = tempfile.mkdtemp()
    try:
        for q in questions:
            instance_name = q.get_name()
            try:
                content = json.dumps(q.answer().dict(), indent=4,
                                     sort_keys=True)
            except BatfishException as e:
                content = "Failed to answer {}: {}".format(instance_name, e)
                bf_logger.warning(content)

            with open(os.path.join(tmp_dir, instance_name), 'w') as f:
                f.write(content)

        tmp_dir_anon = tempfile.mkdtemp()
        _anonymize_dir(tmp_dir, tmp_dir_anon, netconan_config)
    finally:
        shutil.rmtree(tmp_dir)

    if dry_run:
        bf_logger.info(
            'See anonymized files produced by dry-run here: {}'.format(
                tmp_dir_anon))
        return tmp_dir_anon

    try:
        if bucket is None:
            raise ValueError('Bucket must be set to upload init info.')
        if region is None:
            raise ValueError('Region must be set to upload init info.')

        # Generate anonymous S3 subdirectory name
        anon_dir_name = md5(
            '{}{}{}'.format(bf_session.network,
                            bf_session.baseSnapshot,
                            uuid.uuid4().hex).encode()).hexdigest()
        upload_dest = 'https://{bucket}.s3-{region}.amazonaws.com/{resource}'.format(
            bucket=bucket, region=region, resource=anon_dir_name)

        _upload_dir_to_url(upload_dest, tmp_dir_anon,
                           headers={'x-amz-acl': 'bucket-owner-full-control'})
        bf_logger.debug('Uploaded files to: {}'.format(upload_dest))
    finally:
        shutil.rmtree(tmp_dir_anon)

    return anon_dir_name


def _anonymize_dir(input_dir, output_dir, netconan_config=None):
    # type: (str, str, str) -> None
    """
    Anonymize files in input dir and save to output dir.

    Uses Netconan with the provided configuration file to perform anonymization.  If no configuration is provided, only IP addresses and password will be anonymized.

    :param input_dir: directory containing files to anonymize
    :type input_dir: string
    :param output_dir: directory to store anonymized files in
    :type output_dir: string
    :param netconan_config: path to Netconan configuration file
    :type netconan_config: string
    """
    args = [
        '-i', str(input_dir),
        '-o', str(output_dir),
    ]
    if netconan_config is not None:
        args.extend([
            '-c', netconan_config
        ])
    else:
        args.extend([
            '-a',
            '-p',
        ])
    netconan.main(args)


def _check_if_snapshot_passed():
    # type: () -> bool
    """
    Check if current snapshot passed parsing and conversion.

    :return: boolean indicating if all files and nodes in current snapshot passed parsing and conversion
    :rtype: bool
    """
    try:
        answer = _INIT_INFO_QUESTION.answer()
    except BatfishException as e:
        bf_logger.warning(
            "Failed to check snapshot init info: {}".format(e))
        return False

    # These statuses contain parse and conversion status
    statuses = answer['answerElements'][0]['parseStatus']
    for key in statuses:
        if statuses[key] != 'PASSED':
            return False
    return True


def _upload_dir_to_url(base_url, src_dir, headers=None):
    # type: (str, str, Optional[Dict]) -> None
    """
    Recursively put files from the specified directory to the specified URL.

    :param base_url: URL to put files to
    :type base_url: string
    :param src_dir: directory containing files to upload
    :type src_dir: string
    """
    for root, dirs, files in os.walk(src_dir):
        for name in files:
            path = os.path.join(root, name)
            rel_path = os.path.relpath(path, src_dir)
            with open(path, 'rb') as data:
                resource = '{}/{}'.format(base_url, rel_path)
                r = requests.put(resource, data=data, headers=headers)
                if r.status_code != 200:
                    raise HTTPError(
                        'Failed to upload resource: {} with status code {}'.format(
                            resource, r.status_code))
