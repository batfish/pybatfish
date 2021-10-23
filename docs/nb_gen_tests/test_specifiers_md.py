import hashlib
import os
from os.path import abspath, dirname, realpath
from pathlib import Path

import requests

_this_dir = Path(abspath(dirname(realpath(__file__))))
_root_dir = _this_dir.parent.parent


def test_specifiers_up_to_date():
    original = requests.get(
        "https://raw.githubusercontent.com/batfish/batfish/master/questions/Parameters.md"
    ).content
    doc_source_dir = Path(_root_dir) / "docs" / "source"
    checked_in = doc_source_dir / "specifiers.md"
    outfile = doc_source_dir / "specifiers.md.testout"
    if outfile.exists():
        os.remove(outfile)
    if (
        hashlib.sha256(original).hexdigest()
        != hashlib.sha256(checked_in.read_bytes()).hexdigest()
    ):
        outfile.write_bytes(original)
        raise AssertionError("Checked in specifiers.md file is outdated.")
