# Importing required libraries, setting up logging, and loading questions
import logging
import pandas as pd
import random  # noqa: F401
from IPython.display import display
from pandas.io.formats.style import Styler

from pybatfish.client.commands import *  # noqa: F401

# noinspection PyUnresolvedReferences
from pybatfish.datamodel import Edge, Interface
from pybatfish.datamodel.answer import TableAnswer
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints  # noqa: F401
from pybatfish.datamodel.route import BgpRoute  # noqa: F401
from pybatfish.question import bfq, list_questions, load_questions  # noqa: F401
from pybatfish.util import get_html

# Configure all pybatfish loggers to use WARN level
logging.getLogger("pybatfish").setLevel(logging.WARN)

pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_columns", None)
# Prevent rendering text between '$' as MathJax expressions
pd.set_option("display.html.use_mathjax", False)

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
    if isinstance(df, TableAnswer):
        df = df.frame()

    # workaround for Pandas bug in Python 2.7 for empty frames
    if not isinstance(df, pd.DataFrame) or df.size == 0:
        display(df)
        return
    display(
        MyStyler(df)
        .set_uuid(_STYLE_UUID)
        .format(get_html)
        .set_properties(**{"text-align": "left", "vertical-align": "top"})
    )
