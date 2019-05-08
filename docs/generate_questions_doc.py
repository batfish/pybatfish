#!/usr/bin/env python3
# coding=utf-8
"""
Script to generate question template documentation.

For developer use only.

This is a (somewhat hacky) script to update auto-generated
documentation of question templates. It enables a developer to document question
templates using Sphinx, which subsequently allows ReadTheDocs to build
full documentation without needing to clone batfish/load questions first.

This script hardcodes which example snapshot to use and what values to use for
mandatory parameters. It also bets on the fact that question templates won't
need to be re-generated frequently.

The script should have access to a running Batfish service on localhost.
"""
import inspect
import sys
from inspect import getmembers
from os.path import abspath, dirname, realpath, join, pardir
from requests import ConnectionError
from warnings import warn

import pybatfish
from pybatfish.client.options import Options
from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints
from pybatfish.datamodel.answer import TableAnswer
from pybatfish.question import load_questions  # noqa: 402
from pybatfish.question import bfq  # noqa: 402

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir))
sys.path.insert(0, _root_dir)

_questions_to_ignore = [
    "filterTable",  # takes a question as input; no fixed schema
    "testRoutePolicies",  # likely to evolve; need work to support its types
    "viModel"  # not a table answer
]

_example_snapshot_dir = join(_root_dir, 'jupyter_notebooks/networks/example')

# Example values to use for parameters of a given type
_values_by_type = {
    'headerConstraint': HeaderConstraints(dstIps="0.0.0.0/0"),
    'ip': "1.1.1.1",
    'locationSpec': "/.*/",
    'nodeSpec': "/.*/",
}


def _get_mandatory_parameters(template_dict):
    """
    Returns parameter name to type map for parameters are neither optional nor
    have a default value in the template.
    """
    mandatory_params = {}
    all_params = template_dict.get("instance", {}).get("variables", {})
    for p in all_params.items():
        if not p[1].get("optional", False) and "value" not in p[1]:
            mandatory_params[p[0]] = p[1]["type"]
    return mandatory_params


def _get_parameter_values(parameters):
    """
    Returns a parameter name to value map, given a parameter name to type map.

    It does that by using the type to value map.
    """
    parameter_values = {}
    for p in parameters.items():
        if p[1] in _values_by_type:
            parameter_values[p[0]] = _values_by_type[p[1]]
    return parameter_values


def _is_trivial_description(col_name, col_description):
    """
    Heuristics to determine if the column has a trivial description (which we
    do not document).
    """
    return col_description == col_name or \
        col_description == "Property " + col_name or \
        col_description == col_name.replace("_", " ")


def _process(line):
    return "   " + line


if __name__ == "__main__":
    session = None
    try:
        session = Session()
    except ConnectionError as e:
        warn("Could not load question templates from {}: {}\n".format(
            Options.coordinator_host, e) +
             "Documentation will not be generated for questions.")
        sys.exit(1)

    session.set_network("generate_questions")
    snapshot = session.init_snapshot(_example_snapshot_dir,
                                     name="generate_questions", overwrite=True)

    # use extension different from *.rst
    with open(join("source", "questions-generated.rstgen"), 'w') as f:
        # Setup module header
        f.write(".. py:module:: pybatfish.question.bfq\n\n")

        # For each class in bfq, extract and format the constructor's docstring
        for member in getmembers(session.q, inspect.isclass):
            question_name = member[0]
            question_class = member[1]

            if question_name == "__class__":
                continue

            doc_orig = inspect.getdoc(question_class).split("\n")
            doc_updated = "\n".join(_process(line) for line in doc_orig)
            f.write(
                ".. py:class:: {}{}\n\n{}\n\n".format(
                    question_name,
                    inspect.signature(question_class.__init__),
                    doc_updated))

            if question_name in _questions_to_ignore:
                continue

            # Compute the parameter values we are going to use
            template_dict = question_class.template
            mandatory_params = _get_mandatory_parameters(template_dict)
            mandatory_param_values = _get_parameter_values(mandatory_params)

            # Ask the question
            question_instance = question_class(**mandatory_param_values)
            answer = question_instance.answer() if \
                not template_dict.get("differential", False) else \
                question_instance.answer(reference_snapshot=snapshot)
            table_answer = TableAnswer(answer)

            # Output column details as a note
            f.write(_process("Return table columns:\n\n"))
            for col in table_answer.metadata.column_metadata:
                f.write(_process("#. **{}**{}\n\n".format(col.name,
                                                          "" if _is_trivial_description(
                                                              col.name,
                                                              col.description) else " -- {}".format(
                                                              col.description))))
