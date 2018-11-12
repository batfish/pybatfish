#!/usr/bin/env python3
# coding=utf-8
"""
Script to generate question template documentation.

For developer use only.

This is a (somewhat hacky) script to update auto-generated
documentation of question templates. It enables a developer to document question
templates using Sphinx, which subsequently allows ReadTheDocs to build
full documentation without needing to clone batfish/load questions first.

This script makes some assumptions about where questions are located
and bets on the fact that question templates won't need to be re-generated very
frequently.
"""

import inspect
import sys
from inspect import getmembers
from os.path import abspath, dirname, realpath, join, pardir
from warnings import warn

import pybatfish

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir))
sys.path.insert(0, _root_dir)

from pybatfish.question import load_dir_questions  # noqa: 402
from pybatfish.question import bfq  # noqa: 402


def _process(line):
    return "   " + line


if __name__ == "__main__":
    print(_root_dir)
    # Make some assumptions about where questions live
    question_dir = join(_root_dir, 'questions')
    try:
        load_dir_questions(question_dir)
    except FileNotFoundError:
        warn("Could not load question templates from {} ".format(question_dir) +
             "Documentation will not be generated for questions.")

    # use extension different from *.rst
    with open(join("source", "questions-generated.rstgen"), 'w') as f:
        # Setup module header
        f.write(".. py:module:: pybatfish.question.bfq\n\n")

        # For each class in bfq, extract and format the constructor's docstring
        for member in getmembers(pybatfish.question.bfq, inspect.isclass):
            doc_orig = inspect.getdoc(member[1]).split("\n")
            doc_updated = "\n".join(_process(line) for line in doc_orig)
            f.write(
                ".. py:class:: {}{}\n\n{}\n\n".format(
                    member[0],
                    inspect.signature(member[1].__init__),
                    doc_updated))
