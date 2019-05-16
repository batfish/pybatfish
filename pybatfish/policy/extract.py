# coding utf-8
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
"""Handle user specified policies."""

import logging

from pybatfish.client.session import Session
from pybatfish.policy.convert.yaml import convert_yml
from pybatfish.policy.policy import Policy

# TODO remove this crap
logging.getLogger('pybatfish.policy').setLevel(logging.INFO)
logging.getLogger('pybatfish.policy').addHandler(logging.StreamHandler())


def run_policy(name, yaml_file, session=None):
    logger = logging.getLogger(__name__)
    logger.info('Creating policy: {}'.format(name))

    if not session:
        logger.info('No session supplied, creating one')
        session = Session()

    policy = Policy(name, convert_yml(yaml_file))
    return policy.run(session)
