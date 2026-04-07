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

"""Entry point for running the Batfish MCP server (Beta).

.. warning::
    This MCP server is currently in **beta**. The tool names, parameters, and
    return formats may change in future releases without prior notice.

Run with::

    python -m pybatfish.mcp

Or, after installing pybatfish with the ``mcp`` extra::

    batfish-mcp

Session configuration:

Sessions can be configured in ``~/.batfish/sessions.json``::

    {
        "default": {"type": "bf", "params": {"host": "localhost"}},
        "myservice": {"type": "myservice", "params": {"endpoint": "https://..."}}
    }

Or via environment variables:

* ``BATFISH_HOST`` — hostname of the Batfish server (default: ``localhost``).
  Used when no config file is present.
"""

import argparse
from pathlib import Path

from pybatfish.mcp.server import create_server


def main() -> None:
    """Start the Batfish MCP server using stdio transport."""
    parser = argparse.ArgumentParser(description="Batfish MCP server (Beta)")
    parser.add_argument(
        "--sessions-config",
        type=Path,
        default=None,
        help="Path to sessions JSON config file (default: ~/.batfish/sessions.json)",
    )
    args = parser.parse_args()
    server = create_server(sessions_config=args.sessions_config)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
