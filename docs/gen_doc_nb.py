#!/usr/bin/env python3
# coding: utf-8

import inspect
import json
import logging
import re
import sys
import textwrap
from inspect import getmembers
from os.path import abspath, dirname, join, pardir, realpath
from pathlib import Path
from typing import Any, List, Tuple, Mapping, Set
from warnings import warn

import nbformat as nbf
import pandas as pd
import progressbar
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import NotebookNode

from pybatfish.client.commands import *  # noqa: F401
from pybatfish.client.options import Options  # noqa: F401
from pybatfish.datamodel.answer import TableAnswer  # noqa: F401
from pybatfish.question import bfq, load_questions, list_questions  # noqa: F401
from pybatfish.datamodel.primitives import *  # noqa: F401
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints  # noqa: F401
from pybatfish.datamodel.referencelibrary import *  # noqa: F401
from pybatfish.datamodel.referencelibrary import InterfaceGroup  # noqa: F401
from pybatfish.client.asserts import *  # noqa: F401
from pybatfish.question.question import QuestionMeta

BASE_DOCGEN_DIR: Path = Path(abspath(dirname(realpath(__file__))))
BASE_REPO_DIR: Path = BASE_DOCGEN_DIR.parent

base_hc_nb_file: Path = BASE_DOCGEN_DIR / "base-question-notebook.ipynb"
questions_file: Path = BASE_DOCGEN_DIR / "questions.json"

_example_snapshot_dir = BASE_DOCGEN_DIR / "networks" / "example"
_example_snapshot_name = "generate_questions"
_example_snapshot_network = "generate_questions"
_example_snapshot_tuple = (_example_snapshot_name, _example_snapshot_dir)

# to have sphinx hide the cell, when the cell is created we must pass in the
# metadata_hide dict:
metadata_hide = {"nbsphinx": "hidden"}


# e.g.,  nbf.v4.new_markdown_cell(comment, metadata=metadata_hide)
#
# the base notebook already has the metadata set, so no need to set it again here
#


def set_pandas_settings() -> None:
    """Set preferred pandas output settings."""
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.max_rows", 1000)
    pd.set_option("display.max_colwidth", -1)


def to_snake_case(camel_input: str) -> str:
    """Converts camel case to snake case"""
    # https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\d|\W|$)|\d+", camel_input)
    return "-".join(map(str.lower, words))


def gen_query_list(query_list: List[Any]) -> List[NotebookNode]:
    """
    Generates the question section header with the list of questions that are part of the section.
    """
    t_cells = []
    comment = ""

    for item in query_list:
        for k, v in item.items():
            # generate list of queries with links
            type = v.get("type", "basic")
            if type == "skip":
                continue

            comment += "* [{}](#{})\n".format(k, k.replace(" ", "-"))
            comment += "\n"

    t_cells.append(nbf.v4.new_markdown_cell(comment))
    return t_cells


def convert_schema(input_value: str, schema_type: str, question_name: str) -> str:
    """
    Converts the return values from question class into the appropriate type with links to the Batfish datamodel types
    """

    basic_type_map = {
        "integer": "int",
        "long": "int",
        "boolean": "bool",
        "string": "str",
        "double": "double",
    }

    input_type_map = {
        "flow": "pybatfish.datamodel.flow.Flow",
        "trace": "pybatfish.datamodel.flow.Trace",
        "node": "str",
        "headerconstraints": "pybatfish.datamodel.flow.HeaderConstraints",
        "headerconstraint": "pybatfish.datamodel.flow.HeaderConstraints",
        "pathconstraints": "pybatfish.datamodel.flow.PathConstraints",
        "pathconstraint": "pybatfish.datamodel.flow.PathConstraints",
        "filelines": "pybatfish.datamodel.primitives.FileLines",
        "interface": "pybatfish.datamodel.primitives.Interface",
        "bgproute": "pybatfish.datamodel.route.BgpRoute",
        "prefix": "str",
        "vrf": "str",
        "edge": "pybatfish.datamodel.primitives.Edge",
        "ip": "str",
        "javaregex": "str",
        "structurename": "str",
        "comparator": "str",
        "acltrace": "pybatfish.datamodel.acl.AclTrace",
        "acltraceevent": "pybatfish.datamodel.acl.AclTraceEvent",
    }

    output_type_map = {
        "flow": "pybatfish.datamodel.flow.Flow",
        "trace": "pybatfish.datamodel.flow.Trace",
        "flowtrace": "pybatfish.datamodel.flow.FlowTrace",
        "node": "str",
        "headerconstraints": "pybatfish.datamodel.flow.HeaderConstraints",
        "headerconstraint": "pybatfish.datamodel.flow.HeaderConstraints",
        "pathconstraints": "pybatfish.datamodel.flow.PathConstraints",
        "pathconstraint": "pybatfish.datamodel.flow.PathConstraints",
        "filelines": "pybatfish.datamodel.primitives.FileLines",
        "interface": "pybatfish.datamodel.primitives.Interface",
        "bgproute": "pybatfish.datamodel.route.BgpRoute",
        "prefix": "str",
        "vrf": "str",
        "edge": "pybatfish.datamodel.primitives.Edge",
        "ip": "str",
        "structurename": "str",
        "comparator": "str",
        "acltrace": "pybatfish.datamodel.acl.AclTrace",
        "acltraceevent": "pybatfish.datamodel.acl.AclTraceEvent",
    }

    replacement_map = {
        "headerConstraint": "HeaderConstraints",
        "headerConstraints": "HeaderConstraints",
        "pathConstraints": "PathConstraints",
        "pathConstraint": "PathConstraints",
        "interfacesSpec": "interfaceSpec",
        "ipSpaceSpec": "ipSpec",
        "ipSpacesSpec": "ipSpec",
    }
    self_describing_map = {
        "bgpPeerConfiguration": "str",
        "bgpSessionCompatibility": "str",
        "bgpSessionStatus": "str",
        "namedStructures": "dict",
    }

    # deal with java vs python type discrepancies
    value = replacement_map.get(input_value, input_value)

    if value.startswith("Set<"):
        t = re.sub("^Set<", "", value)
        t = re.sub(">", "", t)
        return "Set of {}".format(convert_schema(t, schema_type, question_name))
    elif value.startswith("List<"):
        t = re.sub("^List<", "", value)
        t = re.sub(">", "", t)
        return "List of {}".format(convert_schema(t, schema_type, question_name))
    elif value.lower() in basic_type_map.keys():
        return basic_type_map[value.lower()]
    elif value.endswith("Spec"):
        # specifiers follow a nice pattern, so no need for a manual map
        # convert camel case and add - as seperator
        # then turn spec into specifier
        y = re.sub(r"spec$", "specifier", to_snake_case(value))
        return "[{}](../specifiers.md#{})".format(value, y)
    elif schema_type == "input":
        item = input_type_map.get(value.lower(), value)
        if "datamodel" in item:
            return "[{}](../datamodel.rst#{})".format(value, item)
        else:
            return item
    elif schema_type == "output":
        item = output_type_map.get(value.lower(), value)
        if "datamodel" in item:
            return "[{}](../datamodel.rst#{})".format(value, item)
        elif item.lower() == "selfdescribing":
            try:
                return self_describing_map[question_name]
            except KeyError:
                raise KeyError(
                    f"Error: unknown selfdescribing schema usage in question {question_name}"
                )
        else:
            return item
    else:
        raise ValueError(
            f"Error: Unable to convert based on parameters - value: {value}, type {schema_type}, question {question}"
        )


def gen_output_table(col_data, question) -> str:
    """
    Converts the return values from question class into a markdown table
    """

    table_lines = ["Name | Description | Type", "--- | --- | ---"]
    for col in col_data:
        schema_type = convert_schema(col.schema, "output", question)
        table_lines.append(f"{col.name} | {col.description} | {schema_type}")

    return "\n".join(table_lines)


def gen_input_table(parameters, question) -> str:
    """
    Converts the input parameters from question class into a markdown table
    """
    if not parameters:
        return ""

    table_lines = [
        "Name | Description | Type | Optional | Default Value",
        "--- | --- | --- | --- | --- ",
    ]

    for col in parameters:
        name = col[0]
        desc = col[1]["description"]
        schema_type = convert_schema(col[1]["type"], "input", question)
        optional = col[1].get("optional", "false")
        default_value = ""
        if "value" in col[1].keys():
            default_value = col[1]["value"]
            optional = "true"

        table_lines.append(
            f"{name} | {desc} | {schema_type} | {optional} | {default_value}"
        )

    return "\n".join(table_lines)


def get_desc_and_params(
    question_class: QuestionMeta,
) -> Tuple[str, str, List[Tuple[str, Any]]]:
    """
    Generates the description and parameter information for the question from its class.
    """
    instance = question_class.template["instance"]
    description = instance["description"]
    long_description = instance["longDescription"]

    param_info = []
    for param in inspect.signature(question_class.__init__).parameters:
        if param == "question_name":
            # Skip question name
            continue
        param_info.append((param, instance["variables"][param]))

    return description, long_description, param_info


def gen_query_section(query_list, question_class_map):
    """
    Generates the question documentation
    """

    t_cells = []

    # iterate through list of questions
    for item in query_list:
        for k, v in item.items():
            if v["question"] not in question_class_map:
                warn(
                    "Question '{}' could was not loaded from Batfish. Skipping doc generation for it".format(
                        v["question"]
                    )
                )
                continue

            desc_and_params = get_desc_and_params(question_class_map[v["question"]])
            # TODO: get the cell contents from desc_and_params

            type = v.get("type", "basic")
            parameters = v.get("parameters", "")
            snapshot = tuple(v.get("snapshot", _example_snapshot_tuple))

            if type == "skip":
                continue
            else:
                # setting the network & snapshot here since we have to execute the query to get retrieve column meta-data
                bf_set_network(_example_snapshot_network)
                bf_set_snapshot(snapshot[0])

                content = "bf_set_network('{}')".format(_example_snapshot_network)
                t_cells.append(nbf.v4.new_code_cell(content, metadata=metadata_hide))

                content = "bf_set_snapshot('{}')".format(snapshot[0])
                t_cells.append(nbf.v4.new_code_cell(content, metadata=metadata_hide))

                # Section header which is the question name
                question = "##### {}".format(k)
                t_cells.append(nbf.v4.new_markdown_cell(question))

                comment = "*Description*: {}".format(desc_and_params[0])
                t_cells.append(nbf.v4.new_markdown_cell(comment))

                comment = "*Long Description:* {}".format(desc_and_params[1])
                t_cells.append(nbf.v4.new_markdown_cell(comment))

                comment = "###### Inputs"
                t_cells.append(nbf.v4.new_markdown_cell(comment))

                # generate table describing the output of the query
                input_table = gen_input_table(desc_and_params[2], v["question"])
                t_cells.append(nbf.v4.new_markdown_cell(input_table))

                comment = "###### Invocation"
                t_cells.append(nbf.v4.new_markdown_cell(comment))

                if type == "diff":
                    reference_snapshot = v["reference_snapshot"]
                    expression = "bfq.{}({}).answer(\n\tsnapshot='{}',reference_snapshot='{}')".format(
                        v["question"], parameters, snapshot[0], reference_snapshot[0]
                    )
                    # this results in a very long cell. not sure how to deal with that
                    # need to look into cell wrapping for code cells
                else:
                    expression = "bfq.{}({}).answer()".format(v["question"], parameters)

                column_metadata = TableAnswer(eval(expression)).metadata.column_metadata
                # TODO: get the output column cell contents from column_metadata

                # Code cell to execute question
                content = ">>> result = {}.frame()".format(expression)
                # this didn't help, will need to dig into it some more
                metadata_wrap = {"cm_config": {"lineWrapping": "true"}}
                t_cells.append(nbf.v4.new_code_cell(content, metadata=metadata_wrap))

                comment = "###### Return Value"
                t_cells.append(nbf.v4.new_markdown_cell(comment))

                # generate table describing the output of the query
                output_table = gen_output_table(column_metadata, v["question"])
                t_cells.append(nbf.v4.new_markdown_cell(output_table))

                if type == "basic":
                    comment = "Print the first 5 rows of the returned Dataframe"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.head(5)"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Print the first row of the returned Dataframe"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.iloc[0]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                elif type == "no-result":
                    comment = "Print the first 5 rows of the returned Dataframe"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.head(5)"
                    t_cells.append(nbf.v4.new_code_cell(content))

                elif type == "singleflow":
                    comment = "Retrieving the flow definition"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Flow"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the detailed Trace information"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> len(result.Traces)"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    content = ">>> result.Traces[0]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Evaluating the first Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Traces[0][0]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the disposition of the first Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Traces[0][0].disposition"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the first hop of the first Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Traces[0][0][0]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the last hop of the first Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Traces[0][0][-1]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                elif type == "dualflow":
                    comment = "Retrieving the Forward flow definition"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Forward_Flow"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the detailed Forward Trace information"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> len(result.Forward_Traces)"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    content = ">>> result.Forward_Traces[0]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Evaluating the first Forward Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Forward_Traces[0][0]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the disposition of the first Forward Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Forward_Traces[0][0].disposition"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the first hop of the first Forward Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Forward_Traces[0][0][0]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the last hop of the first Forward Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Forward_Traces[0][0][-1]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the Return flow definition"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Reverse_Flow"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the detailed Return Trace information"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> len(result.Reverse_Traces)"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    content = ">>> result.Reverse_Traces[0]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Evaluating the first Reverse Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Reverse_Traces[0][0]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the disposition of the first Reverse Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Reverse_Traces[0][0].disposition"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the first hop of the first Reverse Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Reverse_Traces[0][0][0]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                    comment = "Retrieving the last hop of the first Reverse Trace"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.Reverse_Traces[0][0][-1]"
                    t_cells.append(nbf.v4.new_code_cell(content))

                elif type == "diff":
                    comment = "Print the first 5 rows of the returned Dataframe"
                    t_cells.append(nbf.v4.new_markdown_cell(comment))

                    content = ">>> result.head(5)"
                    t_cells.append(nbf.v4.new_code_cell(content))

                else:
                    continue

    return t_cells


def load_question_map() -> Mapping[str, QuestionMeta]:
    try:
        load_questions()
    except ConnectionError as e:
        warn(
            "Could not load question templates from {}: {}\n".format(
                Options.coordinator_host, e
            )
            + "Documentation will not be generated for questions."
        )
        sys.exit(1)

    # get a map from question name to class
    question_class_map = {
        name: member for name, member in getmembers(bfq, inspect.isclass)
    }
    if "__class__" in question_class_map:
        del question_class_map["__class__"]  # don't need this member
    return question_class_map


def init_snapshots(questions: Mapping) -> None:
    # collect list of snapshots that need to be initialized
    snapshot_set: Set[Tuple[str]] = set()

    for q_category, v in questions.items():
        # v['questions'] is the list of questions in that category
        for item in v["questions"]:
            # item is the question metadata dictionary
            for q in item.keys():
                snapshot = item[q].get("snapshot", _example_snapshot_tuple)
                # Tuple here is (name, dir)
                snapshot_set.add(tuple(snapshot))

                if item[q].get("type", "basic") == "diff":
                    snapshot = item[q].get(
                        "reference_snapshot", _example_snapshot_tuple
                    )
                    snapshot_set.add(tuple(snapshot))

    logging.info("Initializing snapshots")
    for item in progressbar.progressbar(snapshot_set):
        snapshot_name = item[0]
        snapshot_path = BASE_DOCGEN_DIR / item[1]
        bf_init_snapshot(str(snapshot_path), name=snapshot_name, overwrite=True)


def main() -> None:
    set_pandas_settings()
    progressbar.streams.wrap_stderr()
    logging.basicConfig(format="%(asctime)-15s %(message)s", level=logging.INFO)
    logging.getLogger("pybatfish").setLevel(logging.WARN)

    # get the questions list and associated data to generate the docs
    questions_by_category = json.load(questions_file.open())
    question_class_map = load_question_map()

    bf_set_network(_example_snapshot_network)

    init_snapshots(questions_by_category)

    # iterate through the questions json to create the category specific notebooks
    for q_category, v in progressbar.progressbar(questions_by_category.items()):
        # create notebook object
        nb = nbf.read(base_hc_nb_file.open("r"), as_version=4)

        # initialize array for cells that will be added. copying the cells from base notebook, so can just replace the value in the end
        cells = nb["cells"]

        # out_nb_file = "{}/generated_notebooks/{}.ipynb".format(
        #     BASE_DOCGEN_DIR, k
        # )  # non-executed notebook file
        exec_nb_file = "{}/docs/source/notebooks/{}.ipynb".format(
            BASE_REPO_DIR, q_category
        )  # executed notebook file

        comment = "#### {}".format(questions_by_category[q_category]["comment"])
        cells.append(nbf.v4.new_markdown_cell(comment))

        if q_category == "differentialQuestions":
            comment = textwrap.dedent(
                """
            Most of the Batfish questions can be run differentially by simply adding
            `snapshot=<name of current snapshot>, reference_snapshot=<name of reference snapshot>` in
            `.answer()`

            For example, to view the difference in routing tables between `snapshot1` and `snapshot0`, run
            `bfq.routes().answer(snapshot="snapshot1", reference_snapshot="snapshot0").frame()`

            In addition, Batfish has some questions that can *ONLY* be run differentially.
            They are documented in this section"""
            )
            cells.append(nbf.v4.new_markdown_cell(comment))

        # Creates the list at the top of the page with hyperlinks to each question
        cells.extend(gen_query_list(questions_by_category[q_category]["questions"]))

        # Creates the documentation for each question
        cells.extend(
            gen_query_section(
                questions_by_category[q_category]["questions"], question_class_map
            )
        )

        # overwrite the cells with the fully populated list
        nb["cells"] = cells

        # write non-executed notebook to file
        # with open(out_nb_file, "w") as f:
        #     nbf.write(nb, f)

        logging.info(
            "Executing Notebook for {} category of questions".format(q_category)
        )

        # Execute the notebook and write to file
        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        ep.preprocess(nb, {"metadata": {"path": BASE_DOCGEN_DIR}})

        with open(exec_nb_file, "w", encoding="utf-8") as f:
            nbf.write(nb, f)


if __name__ == "__main__":
    main()
