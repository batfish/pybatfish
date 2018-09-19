# Importing required libraries, setting up logging, and loading questions
import logging

from IPython.display import display
import pandas as pd

from pybatfish.client.commands import *
# noinspection PyUnresolvedReferences
from pybatfish.datamodel.flow import HeaderConstraints
from pybatfish.question import bfq, load_questions  # noqa F401

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
    pd.set_option('max_colwidth', -1)
    # workaround for Pandas bug in Python 2.7 for empty frames
    if df.size == 0:
        display(df)
    else:
        display(df.replace('\n', '<br>', regex=True).replace('  ', '&nbsp;&nbsp;',
                                                         regex=True).style.set_properties(
            **{'text-align': 'left', 'vertical-align': 'top'}))
    pd.set_option('max_colwidth', PD_DEFAULT_COLWIDTH)
