# Importing required libraries, setting up logging, and loading questions
from pybatfish.client.commands import (bf_init_network, bf_set_network,
                                       bf_init_snapshot, bf_generate_dataplane,
                                       bf_logger)  # noqa F401
from pybatfish.question import bfq, load_questions  # noqa F401
from pybatfish.exception import BatfishException  # noqa F401

import logging

bf_logger.setLevel(logging.WARN)

load_questions()
