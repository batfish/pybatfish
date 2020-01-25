# coding: utf-8
from os.path import abspath, dirname, realpath
from pathlib import Path

import pytest
import yaml

from pybatfish.client.session import Session

_THIS_DIR: Path = Path(abspath(dirname(realpath(__file__))))
_DOC_DIR: Path = _THIS_DIR.parent
_QUESTIONS_YAML: Path = _DOC_DIR / "nb_gen" / "questions.yaml"


@pytest.fixture(scope="session")
def session():
    return Session()


@pytest.fixture(scope="session")
def categories():
    return yaml.safe_load(_QUESTIONS_YAML.open())
