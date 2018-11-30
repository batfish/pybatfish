# Importing required libraries, setting up logging, and loading questions
import logging

import pandas as pd
from IPython.display import display
from pandas.io.formats.style import Styler

from pybatfish.client.commands import *
# noinspection PyUnresolvedReferences
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints
from pybatfish.question import bfq, load_questions  # noqa: F401
from pybatfish.util import get_html

bf_logger.setLevel(logging.WARN)

load_questions()

pd.compat.PY3 = True
pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_columns', None)

# UUID for CSS styles used by pandas styler.
# Keeps our notebook HTML deterministic when displaying dataframes
_STYLE_UUID = "pybfstyle"


class MyStyler(Styler):
    """A custom styler for displaying DataFrames in HTML"""

    def __repr__(self):
        return repr(self.data)


def show(df):
    """
    Displays a dataframe as HTML table.

    Replaces newlines and double-spaces in the input with HTML markup, and
    left-aligns the text.
    """

    # workaround for Pandas bug in Python 2.7 for empty frames
    if not isinstance(df, pd.DataFrame) or df.size == 0:
        display(df)
        return
    df = df.replace('\n', '<br>', regex=True).replace('  ', '&nbsp;&nbsp;',
                                                      regex=True)
    display(MyStyler(df).set_uuid(_STYLE_UUID).format(get_html)
            .set_properties(**{'text-align': 'left', 'vertical-align': 'top'}))

from pybatfish.datamodel import Interface, Edge
