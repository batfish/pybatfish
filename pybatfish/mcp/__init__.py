# Copyright 2018 The Batfish Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MCP (Model Context Protocol) server for Batfish (Beta).

.. warning::
    This MCP server is currently in **beta**. The tool names, parameters, and
    return formats may change in future releases without prior notice.

This package provides an official MCP server that exposes Batfish network
analysis capabilities as MCP tools, enabling AI agents (such as Claude,
Cursor, and other MCP-compatible clients) to interact with Batfish for
network configuration analysis and verification.

Usage::

    # Run the MCP server (stdio transport, for use with MCP clients):
    python -m pybatfish.mcp

    # Or run with a specific Batfish host:
    BATFISH_HOST=my-batfish-host python -m pybatfish.mcp

    # Or configure sessions in ~/.batfish/sessions.json:
    # {"default": {"type": "bf", "params": {"host": "localhost"}}}
"""

from pybatfish.mcp.server import create_server

__all__ = ["create_server"]
