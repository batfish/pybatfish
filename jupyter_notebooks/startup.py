# Importing required libraries, setting up logging, and loading questions
import logging

import pandas as pd
from IPython.display import display, HTML

from pybatfish.client.commands import *
# noinspection PyUnresolvedReferences
from pybatfish.question import bfq, list_questions, load_questions  # noqa F401

bf_logger.setLevel(logging.WARN)

load_questions()

pd.compat.PY3 = True
PD_DEFAULT_COLWIDTH = 250
pd.set_option('max_colwidth', PD_DEFAULT_COLWIDTH)

def display_html(df):
    pd.set_option('max_colwidth', -1)
    display(HTML(df.to_html().replace("\\n","<br>") ) )
    pd.set_option('max_colwidth', PD_DEFAULT_COLWIDTH)
    