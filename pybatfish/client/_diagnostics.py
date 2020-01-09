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
from typing import Any, Dict, Iterable, Optional, TYPE_CHECKING  # noqa: F401

import requests
from netconan import netconan
from requests import HTTPError

from pybatfish.datamodel.answer import Answer  # noqa: F401
from pybatfish.exception import BatfishException
from pybatfish.question.question import QuestionBase

if TYPE_CHECKING:
    from pybatfish.client.session import Session  # noqa: F401

METADATA_FILENAME = "metadata"

_FILE_PARSE_STATUS_QUESTION = {
    "class": "org.batfish.question.initialization.FileParseStatusQuestion",
    "differential": False,
    "instance": {"instanceName": "__fileParseStatus"},
}
_INIT_INFO_QUESTION = {
    "class": "org.batfish.question.InitInfoQuestionPlugin$InitInfoQuestion",
    "differential": False,
    "instance": {"instanceName": "__initInfo"},
}
_INIT_ISSUES_QUESTION = {
    "class": "org.batfish.question.initialization.InitIssuesQuestion",
    "differential": False,
    "instance": {"instanceName": "__initIssues"},
}

# Note: this is a Tuple to enforce immutability.
_INIT_INFO_QUESTIONS = (
    _INIT_INFO_QUESTION,
    _INIT_ISSUES_QUESTION,
    _FILE_PARSE_STATUS_QUESTION,
)

_S3_BUCKET = "batfish-diagnostics"
_S3_REGION = "us-west-2"


def upload_diagnostics(
    session: "Session",
    metadata: Dict[str, Any],
    bucket: str = _S3_BUCKET,
    region: str = _S3_REGION,
    dry_run: bool = True,
    netconan_config: Optional[str] = None,
    questions: Iterable[Dict[str, Any]] = _INIT_INFO_QUESTIONS,
    resource_prefix: str = "",
    proxy: Optional[str] = None,
) -> str:
    """
    Fetch, anonymize, and optionally upload snapshot initialization information.

    :param session: Batfish session to use for running diagnostics questions
    :type session: :class:`~pybatfish.client.session.Session`
    :param metadata: additional metadata to upload with the diagnostics
    :type metadata: dict[str, Any]
    :param bucket: name of the AWS S3 bucket to upload to
    :type bucket: string
    :param region: name of the region containing the bucket
    :type region: string
    :param dry_run: if True, upload is skipped and the anonymized files will be stored locally for review. If False, anonymized files will be uploaded to the specified S3 bucket
    :type dry_run: bool
    :param netconan_config: path to Netconan configuration file
    :type netconan_config: string
    :param questions: list of question templates to run and upload
    :type questions: list[QuestionBase]
    :param resource_prefix: prefix to append to any uploaded resources
    :type resource_prefix: str
    :param proxy: proxy URL to use when uploading data.
    :return: location of anonymized files (local directory if doing dry run, otherwise upload ID)
    :rtype: string
    """
    logger = logging.getLogger(__name__)
    tmp_dir = tempfile.mkdtemp()
    try:
        for template in questions:
            q = QuestionBase(template, session)
            instance_name = q.get_name()
            try:
                ans = q.answer()
                if not isinstance(ans, Answer):
                    raise BatfishException(
                        "question.answer() did not return an Answer: {}".format(ans)
                    )
                content = json.dumps(ans.dict(), indent=4, sort_keys=True)
            except BatfishException as e:
                content = "Failed to answer {}: {}".format(instance_name, e)
                logger.warning(content)

            with open(os.path.join(tmp_dir, instance_name), "w") as f:
                f.write(content)

        tmp_dir_anon = tempfile.mkdtemp()
        if questions:
            _anonymize_dir(tmp_dir, tmp_dir_anon, netconan_config)
    finally:
        shutil.rmtree(tmp_dir)

    with open(os.path.join(tmp_dir_anon, METADATA_FILENAME), "w") as f:
        f.write(json.dumps(metadata))

    if dry_run:
        logger.info(
            "See anonymized files produced by dry-run here: {}".format(tmp_dir_anon)
        )
        return tmp_dir_anon

    try:
        if bucket is None:
            raise ValueError("Bucket must be set to upload init info.")
        if region is None:
            raise ValueError("Region must be set to upload init info.")

        # Generate anonymous S3 subdirectory name
        anon_dir = "{}{}".format(resource_prefix, uuid.uuid4().hex)
        upload_dest = "https://{bucket}.s3-{region}.amazonaws.com/{resource}".format(
            bucket=bucket, region=region, resource=anon_dir
        )

        _upload_dir_to_url(
            upload_dest,
            tmp_dir_anon,
            headers={"x-amz-acl": "bucket-owner-full-control"},
            proxies={"https": proxy} if proxy is not None else None,
        )
        logger.debug("Uploaded files to: {}".format(upload_dest))
    finally:
        shutil.rmtree(tmp_dir_anon)

    return anon_dir


def _anonymize_dir(
    input_dir: str, output_dir: str, netconan_config: Optional[str] = None
) -> None:
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
    args = ["-i", str(input_dir), "-o", str(output_dir)]
    if netconan_config is not None:
        args.extend(["-c", netconan_config])
    else:
        args.extend(["-a", "-p"])
    netconan.main(args)


def get_snapshot_parse_status(session):
    # type: (Session) -> Dict[str, str]
    """
    Get parsing and conversion status for files and nodes in the current snapshot.

    :param session: Batfish session to use for getting snapshot parse status
    :type session: :class:`~pybatfish.client.session.Session`
    :return: dictionary of files and nodes to parse/convert status
    :rtype: dict
    """
    parse_status = {}  # type: Dict[str, str]
    try:
        answer = QuestionBase(_INIT_INFO_QUESTION, session).answer()
        if not isinstance(answer, Answer):
            raise BatfishException(
                "question.answer() did not return an Answer: {}".format(answer)
            )

        if "answerElements" not in answer:
            raise BatfishException("Invalid answer format for init info")
        answer_elements = answer["answerElements"]
        if not len(answer_elements):
            raise BatfishException("Invalid answer format for init info")
        # These statuses contain parse and conversion status
        parse_status = answer_elements[0].get("parseStatus", {})
    except BatfishException as e:
        logging.getLogger(__name__).warning("Failed to check snapshot init info: %s", e)

    return parse_status


def check_if_all_passed(statuses):
    # type: (Dict[str, str]) -> bool
    """
    Check if all items in supplied `statuses` dict passed parsing and conversion.

    :param statuses: dictionary init info statuses (files/nodes to their status)
    :type statuses: dict
    :return: boolean indicating if all files and nodes in current snapshot passed parsing and conversion
    :rtype: bool
    """
    return all(statuses[key] == "PASSED" for key in statuses)


def check_if_any_failed(statuses):
    # type: (Dict[str, str]) -> bool
    """
    Check if any item in supplied `statuses` dict failed parsing or conversion.

    :param statuses: dictionary init info statuses (files/nodes to their status)
    :type statuses: dict
    :return: boolean indicating if any file or node in current snapshot failed parsing or conversion
    :rtype: bool
    """
    return any(statuses[key] == "FAILED" for key in statuses)


def _upload_dir_to_url(
    base_url: str,
    src_dir: str,
    headers: Optional[Dict] = None,
    proxies: Optional[Dict] = None,
) -> None:
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
            with open(path, "rb") as data:
                resource = "{}/{}".format(base_url, rel_path)
                r = requests.put(resource, data=data, headers=headers, proxies=proxies)
                if r.status_code != 200:
                    raise HTTPError(
                        "Failed to upload resource: {} with status code {}".format(
                            resource, r.status_code
                        )
                    )


def warn_on_snapshot_failure(session):
    # type: (Session) -> None
    """
    Check if snapshot passed and warn about any parsing or conversion issues.

    :param session: Batfish session to check for snapshot failure
    :type session: :class:`~pybatfish.client.session.Session`
    """
    logger = logging.getLogger(__name__)
    statuses = get_snapshot_parse_status(session)
    if check_if_any_failed(statuses):
        logger.warning(
            """\
Your snapshot was initialized but Batfish failed to parse one or more input files. You can proceed but some analyses may be incorrect. You can help the Batfish developers improve support for your network by running:

    bf_upload_diagnostics(dry_run=False, contact_info='<optional email address>')

to share private, anonymized information. For more information, see the documentation with:

    help(bf_upload_diagnostics)"""
        )
    elif not check_if_all_passed(statuses):
        logger.warning(
            """\
Your snapshot was successfully initialized but Batfish failed to fully recognized some lines in one or more input files. Some unrecognized configuration lines are not uncommon for new networks, and it is often fine to proceed with further analysis. You can help the Batfish developers improve support for your network by running:

    bf_upload_diagnostics(dry_run=False, contact_info='<optional email address>')

to share private, anonymized information. For more information, see the documentation with:

    help(bf_upload_diagnostics)"""
        )
