# Importing required libraries, setting up logging, and loading questions
from pybatfish.client.commands import (bf_init_network, bf_set_network,
                                       bf_init_snapshot, bf_generate_dataplane,
                                       bf_logger)
from pybatfish.question import bfq, load_questions
from pybatfish.exception import BatfishException

import logging

bf_logger.setLevel(logging.WARN)

load_questions()

