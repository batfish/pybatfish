# coding: utf-8
import re
from operator import itemgetter

import pytest
from nb_gen.doc_tables import (
    get_desc_and_params,
    get_input_table_lines,
    get_output_table_lines,
)

from pybatfish.client.session import Session
from pybatfish.datamodel.answer.table import ColumnMetadata


@pytest.fixture(scope="module")
def session() -> Session:
    return Session()


def test_parameter_extraction(session: Session):
    """Test that we extract parameter info from QuestionMeta classes correctly"""
    _, _, params = get_desc_and_params(session.q.nodeProperties)
    params = sorted(params, key=itemgetter(0))
    assert len(params) == 2
    name, pdict = params[0]
    assert name == "nodes"
    assert pdict["type"] == "nodeSpec"
    assert pdict["optional"]

    name, pdict = params[1]
    assert name == "properties"
    assert pdict["type"] == "nodePropertySpec"
    assert pdict["optional"]


def test_get_input_table_lines(session: Session):
    lines = get_input_table_lines(
        get_desc_and_params(session.q.nodeProperties)[2], "nodeProperties"
    )
    # skip first two lines, markdown header
    assert re.match(r"nodes |[\w\s]+|nodeSpec|True|", lines[2])
    assert re.match(r"properties |[\w\s]+|nodeSpec|True|", lines[3])


def test_get_output_table_lines():
    lines = get_output_table_lines(
        [ColumnMetadata(dict(name="Column", description="Dear Abby", schema="String"))],
        "qname",
    )
    assert lines[2] == "Column | Dear Abby | str"
