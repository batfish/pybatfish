# Importing required libraries, setting up logging, and loading questions
import logging

import pandas as pd
from IPython.display import display

from pybatfish.client.commands import *
# noinspection PyUnresolvedReferences
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints
from pybatfish.question import bfq, load_questions  # noqa: F401
from pybatfish.util import get_html

bf_logger.setLevel(logging.WARN)

load_questions()

pd.compat.PY3 = True
PD_DEFAULT_COLWIDTH = 250
pd.set_option('max_colwidth', PD_DEFAULT_COLWIDTH)


def display_html(df):
    """
    Displays a dataframe as HTML table.

    Replaces newlines and double-spaces in the input with HTML markup, and
    left-aligns the text.
    """
    pd.set_option('display.max_colwidth', -1)
    pd.set_option('display.max_columns', None)

    # workaround for Pandas bug in Python 2.7 for empty frames
    if df.size == 0:
        display(df)
    else:
        display(
            df.replace('\n', '<br>', regex=True)
                .replace('  ', '&nbsp;&nbsp;', regex=True)
                .style
                .format(get_html)
                .set_properties(
                **{'text-align': 'left', 'vertical-align': 'top'}))
