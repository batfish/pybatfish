# Importing required libraries, setting up logging, and loading questions
from pybatfish.client.commands import *
from pybatfish.question import bfq, load_questions, list_questions  # noqa F401
from pybatfish.exception import BatfishException  # noqa F401

import logging
import pandas as pd

bf_logger.setLevel(logging.WARN)

load_questions()
list_questions()

pd.compat.PY3 = True
pd.set_option('max_colwidth', 250)
