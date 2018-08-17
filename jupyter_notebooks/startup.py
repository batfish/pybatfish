# Importing required libraries, setting up logging, and loading questions
import logging

import pandas as pd

from pybatfish.client.commands import *
# noinspection PyUnresolvedReferences
from pybatfish.question import bfq, list_questions, load_questions  # noqa F401

bf_logger.setLevel(logging.WARN)

load_questions()

pd.compat.PY3 = True
pd.set_option('max_colwidth', 250)
