# Importing required libraries, setting up logging, and loading questions
from pybatfish.client.commands import *
from pybatfish.question import bfq, load_questions  # noqa F401
from pybatfish.exception import BatfishException  # noqa F401
import pandas as pd

import logging

bf_logger.setLevel(logging.WARN)

load_questions()
pd.set_option('max_colwidth',250)
