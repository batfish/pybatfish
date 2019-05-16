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
"""Convert YAML file into validation tasks."""
import logging

import yaml

from pybatfish.policy.commands import SetNetwork, InitSnapshot, ShowFacts

_BF_COMMANDS = 'bf_commands'
# Supported bf_commands
_CMD_SET_NETWORK = 'set_network'
_CMD_INIT_SNAPSHOT = 'init_snapshot'
_CMD_SHOW_FACTS = 'show_facts'


def convert_yml(filename):
    """Convert specified file into validation commands."""
    logger = logging.getLogger(__name__)

    logger.info('Parsing YAML file: {}'.format(filename))
    with open(filename, 'r') as f:
        yaml_dict = yaml.load(f)
    logger.debug('Extracted YAML: {}'.format(yaml_dict))

    cmds_in = yaml_dict.get(_BF_COMMANDS)
    if not cmds_in:
        raise ValueError(
            'Commands must be specified under top-level key {}'.format(
                _BF_COMMANDS))

    cmds_out = []
    for cmd_dict in cmds_in:
        logger.debug('Command: {}'.format(cmd_dict))
        if len(cmd_dict) != 1:
            raise ValueError(
                'Got malformed command. Expecting single key-value pair '
                'but got: {}'.format(
                    cmd_dict))
        cmd = next(iter(cmd_dict))
        cmd_params = cmd_dict[cmd]

        if cmd == _CMD_SET_NETWORK:
            new_cmd = _extract_network(cmd_params)
        elif cmd == _CMD_INIT_SNAPSHOT:
            new_cmd = _extract_snapshot(cmd_params)
        elif cmd == _CMD_SHOW_FACTS:
            new_cmd = _extract_show_facts(cmd_params)
        else:
            raise ValueError('Got unexpected command: {}'.format(cmd))
        cmds_out.append(new_cmd)

    return cmds_out


def _extract_show_facts(dict_):
    """Extract fact-extractions from input dict."""
    nodes = dict_.get('nodes', None)
    return ShowFacts(nodes)


def _extract_network(name):
    """Create init network command."""
    return SetNetwork(name)


def _extract_snapshot(dict_):
    """Extract snapshot init from input dict."""
    path = dict_.get('path', None)
    overwrite = dict_.get('overwrite', False)
    name = dict_.get('name', None)
    if not path:
        raise ValueError('Snapshot path must be set via \'path\'')
    return InitSnapshot(name, path, overwrite)
