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
from collections import defaultdict, OrderedDict
from inspect import getmembers
from os.path import abspath, dirname, realpath, join, pardir
from typing import List, Dict, TextIO, Any

from requests import ConnectionError
from warnings import warn

from pybatfish.client.options import Options
from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints
from pybatfish.datamodel.answer import TableAnswer

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir))
sys.path.insert(0, _root_dir)

_questions_to_ignore_for_columns = [
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

# mapping from question category tags to category name and description
# the master list of categories being checked and enforced is here: https://github.com/batfish/batfish/blob/master/tests/questions/test_questions.py
_question_categories = OrderedDict(
    [("configuration",
      ["Configuration data questions",
       "Questions that return the contents of configuration in a structured format."]),
     ("hygiene",
      ["Configuration hygiene questions",
       "Questions that flag unused and undefined structures in configurations."]),
     ("status",
      ["Configuration compatibility questions",
       "Questions that show if configuration settings are compatible across devices."]),
     ("topology",
      ["Network adjacency questions",
       "Questions that show different types of network adjacencies."]),
     ("traceroute",
      ["Flow path questions",
       "Questions that show paths of specified flows in the network."]),
     ("reachability",
      ["Flow search questions",
       "Questions that exhaustively search for flows that meet specified constraints."]),
     ("acl",
      ["ACL and firewall analysis questions",
       "Questions that analyze ACLs and firewall rules."]),
     ("routing",
      ["Routing analysis questions",
       "Questions that analyze routing"]),
     ("specifiers",
      ["Specifier resolvers",
       "Questions that resolve specifier expressions."]),
     ("initialization",
      ["Initialization information questions",
       "Question that reveal how well Batfish understood input data."]),
     ("other",
      ["Other questions",
       "Questions that do not belong to any other category"])
     ])

# the category we use when the tags do not let us infer a category
_default_question_category_tag = "other"


def _add_leading_whitespace(line):
    # type: (str) -> str
    return "   " + line


def _categorize_question(question_name, tags):
    # type: (str, List[str]) -> str
    """
    Return the category tag from the list of specified tags

    :param question_name: The name of question, used for the error messages only
    :param tags: The list of tags
    """
    for category_tag in _question_categories.keys():
        if category_tag in tags:
            return category_tag
    # since we are testing in Batfish for the presence of exactly one category
    # tag in each template, this should happen only if categories in this script
    # are out of sync with Batfish (https://github.com/batfish/batfish/blob/master/tests/questions/test_questions.py)
    warn("Could not find a category for {}. Using '{}'".format(question_name,
                                                               _default_question_category_tag))
    return _default_question_category_tag


def _categorize_questions(questions):
    # type: (Dict) -> Dict[str, List[str]]
    """
    Returns a map from category tag to list of question names.

    :param questions: a map from question name to class
    """
    questions_by_category_tag = defaultdict(list)  # type: Dict[str, List[str]]
    for question_name, question_class in questions.items():
        template_dict = question_class.template
        tags = template_dict.get("instance").get("tags")
        category_tag = _categorize_question(question_name, tags)
        questions_by_category_tag[category_tag].append(question_name)
    return questions_by_category_tag


def _get_mandatory_parameters(template_dict):
    # type: (Dict) -> Dict[str, str]
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
    # type: (Dict[str, str]) -> Dict[str, Any]
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
    # type: (str, str) -> bool
    """
    Heuristics to determine if the column has a trivial description (which we
    do not document).
    """
    return col_description == col_name or \
           col_description == "Property " + col_name or \
           col_description == col_name.replace("_", " ")


def _write_question_category(category_tag, tag_questions, all_questions, f):
    # type: (str, List[str], Dict[str, Any], TextIO) -> None
    """
    Writes the section corresponding to the specified category

    :param category_tag: The tag of the category to write.
    :param tag_questions: List of question names in the category.
    :param all_questions: A map from question name to class.
    :param f: File handle to write to.
    """

    # print the header
    # .. _category_tag:
    #
    # category name
    # -------------
    #
    # category description
    #
    f.write(".. _{}:\n\n".format(category_tag))
    f.write(_question_categories[category_tag][0] + "\n")
    f.write("-" * len(_question_categories[category_tag][0]) + "\n\n")
    f.write(_question_categories[category_tag][1] + "\n\n")

    for question_name in tag_questions:
        question_class = all_questions[question_name]

        doc_orig = inspect.getdoc(question_class).split("\n")
        doc_updated = "\n".join(
            _add_leading_whitespace(line) for line in doc_orig)
        f.write(
            ".. py:class:: {}{}\n\n{}\n\n".format(
                question_name,
                inspect.signature(question_class.__init__),
                doc_updated))

        if question_name in _questions_to_ignore_for_columns:
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
        f.write(_add_leading_whitespace("Return table columns:\n\n"))
        for col in table_answer.metadata.column_metadata:
            f.write(_add_leading_whitespace("#. **{}**{}\n\n".format(col.name,
                                                                     "" if _is_trivial_description(
                                                                         col.name,
                                                                         col.description) else " -- {}".format(
                                                                         col.description + (
                                                                             # add period if missing
                                                                             "" if col.description.endswith(
                                                                                 ".") else ".")))))


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
        # write question category list
        for tag, details in _question_categories.items():
            f.write(" - `{} <#{}>`_\n".format(details[0], tag))

        # Setup module header
        f.write("\n")
        f.write(".. py:module:: pybatfish.question.bfq\n\n\n")

        # get a map from question name to class
        all_questions = {q[0]: q[1] for q in
                         getmembers(session.q, inspect.isclass)}
        all_questions.pop("__class__")  # don't need this member

        questions_by_category_tag = _categorize_questions(all_questions)

        # For each class in bfq, extract and format the constructor's docstring
        for category_tag in _question_categories.keys():
            _write_question_category(category_tag,
                                     questions_by_category_tag.get(category_tag,
                                                                   []),
                                     all_questions, f)
