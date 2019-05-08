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

Run the script using "make questions_doc" which will generate an .out file for
questions for which column detail generation failed. Some failures are expected
(3 questions at the time of this writing).
"""
import importlib
import inspect
import sys
from inspect import getmembers
from os.path import abspath, dirname, realpath, join, pardir
from requests import ConnectionError
from warnings import warn

import pybatfish
from pybatfish.client.commands import bf_set_network, bf_set_snapshot, \
    bf_init_snapshot
from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints
from pybatfish.datamodel.answer import TableAnswer
from pybatfish.exception import QuestionValidationException
from pybatfish.question import load_questions  # noqa: 402
from pybatfish.question import bfq  # noqa: 402

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir))
sys.path.insert(0, _root_dir)

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


def _process(line):
    return "   " + line


if __name__ == "__main__":
    session = Session(load_questions=False)
    try:
        load_questions(session=session)
    except ConnectionError:
        warn("Could not load question templates from {}.".format(session.host) +
             "Documentation will not be generated for questions.")

    session.set_network("generate_questions")
    snapshot = session.init_snapshot(_example_snapshot_dir,
                                     name="generate_questions", overwrite=True)

    bfq_module = importlib.import_module("pybatfish.question.bfq")

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

            try:
                # Compute the parameter values we are going to use
                template_dict = member[1].template
                mandatory_params = _get_mandatory_parameters(template_dict)
                mandatory_param_values = _get_parameter_values(mandatory_params)

                # Get the class of the question and instantiate it
                class_ = getattr(bfq_module, member[0])
                instance = class_(**mandatory_param_values)

                # Ask the question
                answer = instance.answer() if \
                    not template_dict.get("differential", False) else \
                    instance.answer(reference_snapshot=snapshot)
                table_answer = TableAnswer(answer)

                # Output column details as a note
                f.write(_process(".. note::\n"))
                f.write(_process(
                    _process("The output table has the following columns\n\n")))
                for col in table_answer.metadata.column_metadata:
                    f.write(_process(_process(
                        "#. **{}** (*{}*) {}\n\n".format(col.name, col.schema,
                                                         col.description))))
            except (QuestionValidationException, ValueError) as e:
                print("Exception while asking {}: {}".format(member[0], e))
