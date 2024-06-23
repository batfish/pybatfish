# coding: utf-8
import inspect
import logging
from collections import namedtuple
from copy import deepcopy
from os.path import abspath, dirname, realpath
from pathlib import Path
from typing import Any, List, Mapping, Set, Tuple

import nbformat
import pandas as pd
import progressbar
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import NotebookNode
from yaml import safe_load

from pybatfish.client.session import Session
from pybatfish.datamodel import *  # noqa: F401
from pybatfish.question.question import QuestionMeta

from .doc_tables import gen_input_table, gen_output_table, get_desc_and_params

_THIS_DIR: Path = Path(abspath(dirname(realpath(__file__))))
_DOC_DIR: Path = _THIS_DIR.parent
_EXEC_NOTEBOOK_DIR: Path = _DOC_DIR / "source" / "notebooks"
_BASE_Q_NOTEBOOK_FILE: Path = _THIS_DIR / "base-question-notebook.ipynb"
_QUESTIONS_FILE: Path = _THIS_DIR / "questions.yaml"
NETWORK_NAME = "generate_questions"
_example_snapshot_config = {
    "name": "generate_questions",
    "path": _DOC_DIR / "networks" / "example",
}

# to have sphinx hide the cell, when the cell is created we must pass in the
# metadata_hide dict:
metadata_hide = {"nbsphinx": "hidden"}


def set_pandas_settings() -> None:
    """Set preferred pandas output settings."""
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_rows", 1000)
    pd.set_option("display.max_colwidth", None)


def load_questions_yaml(fpath: Path) -> Mapping[str, Any]:
    """Loads the YAML describing question categories and how to execute questions."""
    return safe_load(fpath.read_bytes())


def generate_category_toc(question_list: List[Mapping[str, Any]]) -> NotebookNode:
    """Generates table of contents for a question category page."""
    toc_lines = []

    # generate list of questions with links
    for question_data in question_list:
        question_name = question_data["name"]
        link_anchor = question_name.replace(" ", "-")
        toc_lines.append(f"* [{question_name}](#{link_anchor})")

    return nbformat.v4.new_markdown_cell("\n".join(toc_lines))


def generate_result_examination(cells: List[NotebookNode], question_type: str) -> None:
    """Generate notebook cells that expain how to interpret results returned from a given question (depending on question type)."""
    if question_type == "basic":
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Print the first 5 rows of the returned Dataframe"
            )
        )
        cells.append(nbformat.v4.new_code_cell("result.head(5)"))
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Print the first row of the returned Dataframe"
            )
        )
        cells.append(nbformat.v4.new_code_cell("result.iloc[0]"))

    elif question_type == "no-result":
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Print the first 5 rows of the returned Dataframe"
            )
        )
        cells.append(nbformat.v4.new_code_cell("result.head(5)"))
    elif question_type == "singleflow":
        cells.append(nbformat.v4.new_markdown_cell("Retrieving the flow definition"))
        cells.append(nbformat.v4.new_code_cell("result.Flow"))
        cells.append(
            nbformat.v4.new_markdown_cell("Retrieving the detailed Trace information")
        )
        cells.append(nbformat.v4.new_code_cell("len(result.Traces)"))
        cells.append(nbformat.v4.new_code_cell("result.Traces[0]"))
        cells.append(nbformat.v4.new_markdown_cell("Evaluating the first Trace"))
        cells.append(nbformat.v4.new_code_cell("result.Traces[0][0]"))
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Retrieving the disposition of the first Trace"
            )
        )
        cells.append(nbformat.v4.new_code_cell("result.Traces[0][0].disposition"))
        cells.append(
            nbformat.v4.new_markdown_cell("Retrieving the first hop of the first Trace")
        )
        cells.append(nbformat.v4.new_code_cell("result.Traces[0][0][0]"))
        cells.append(
            nbformat.v4.new_markdown_cell("Retrieving the last hop of the first Trace")
        )
        cells.append(nbformat.v4.new_code_cell("result.Traces[0][0][-1]"))

    elif question_type == "dualflow":
        cells.append(
            nbformat.v4.new_markdown_cell("Retrieving the Forward flow definition")
        )
        cells.append(nbformat.v4.new_code_cell("result.Forward_Flow"))
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Retrieving the detailed Forward Trace information"
            )
        )
        cells.append(nbformat.v4.new_code_cell("len(result.Forward_Traces)"))
        cells.append(nbformat.v4.new_code_cell("result.Forward_Traces[0]"))
        cells.append(
            nbformat.v4.new_markdown_cell("Evaluating the first Forward Trace")
        )
        cells.append(nbformat.v4.new_code_cell("result.Forward_Traces[0][0]"))
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Retrieving the disposition of the first Forward Trace"
            )
        )
        cells.append(
            nbformat.v4.new_code_cell("result.Forward_Traces[0][0].disposition")
        )
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Retrieving the first hop of the first Forward Trace"
            )
        )
        cells.append(nbformat.v4.new_code_cell("result.Forward_Traces[0][0][0]"))
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Retrieving the last hop of the first Forward Trace"
            )
        )
        cells.append(nbformat.v4.new_code_cell("result.Forward_Traces[0][0][-1]"))
        cells.append(
            nbformat.v4.new_markdown_cell("Retrieving the Return flow definition")
        )
        cells.append(nbformat.v4.new_code_cell("result.Reverse_Flow"))
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Retrieving the detailed Return Trace information"
            )
        )
        cells.append(nbformat.v4.new_code_cell("len(result.Reverse_Traces)"))
        cells.append(nbformat.v4.new_code_cell("result.Reverse_Traces[0]"))
        cells.append(
            nbformat.v4.new_markdown_cell("Evaluating the first Reverse Trace")
        )
        cells.append(nbformat.v4.new_code_cell("result.Reverse_Traces[0][0]"))
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Retrieving the disposition of the first Reverse Trace"
            )
        )
        cells.append(
            nbformat.v4.new_code_cell("result.Reverse_Traces[0][0].disposition")
        )
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Retrieving the first hop of the first Reverse Trace"
            )
        )
        cells.append(nbformat.v4.new_code_cell("result.Reverse_Traces[0][0][0]"))
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Retrieving the last hop of the first Reverse Trace"
            )
        )
        cells.append(nbformat.v4.new_code_cell("result.Reverse_Traces[0][0][-1]"))
    elif question_type == "diff":
        cells.append(
            nbformat.v4.new_markdown_cell(
                "Print the first 5 rows of the returned Dataframe"
            )
        )
        cells.append(nbformat.v4.new_code_cell("result.head(5)"))

    else:
        raise ValueError(f"Unknown question type: {question_type}")


def generate_code_for_question(
    question_data: Mapping[str, Any],
    question_class_map: Mapping[str, QuestionMeta],
    session: Session,
) -> List[NotebookNode]:
    """Generate notebook cells for a single question."""
    question_type = question_data.get("type", "basic")
    if question_type == "skip":
        return []
    cells: List[NotebookNode] = []
    pybf_name = question_data["pybf_name"]
    if pybf_name not in question_class_map:
        raise KeyError(f"Unknown pybf question: {pybf_name}")
    q_class: QuestionMeta = question_class_map[pybf_name]

    snapshot_config = question_data.get("snapshot", _example_snapshot_config)

    # setting the network & snapshot here since we have to execute the query to get retrieve column meta-data
    session.set_network(NETWORK_NAME)
    snapshot_name = snapshot_config["name"]
    session.set_snapshot(snapshot_name)

    # creating the var bf as the BF session object so that the notebooks
    # can use bf. calls, but the notebook generation code will use
    # session.
    bf = session  # noqa: F401

    cells.append(
        nbformat.v4.new_code_cell(
            f"bf.set_network('{NETWORK_NAME}')", metadata=metadata_hide
        )
    )
    cells.append(
        nbformat.v4.new_code_cell(
            f"bf.set_snapshot('{snapshot_name}')", metadata=metadata_hide
        )
    )
    description, long_description, params = get_desc_and_params(q_class)
    # Section header which is the question name
    cells.append(nbformat.v4.new_markdown_cell(f"##### {question_data.get('name')}"))
    cells.append(nbformat.v4.new_markdown_cell(f"{description}"))
    cells.append(nbformat.v4.new_markdown_cell(f"{long_description}"))
    cells.append(nbformat.v4.new_markdown_cell("###### **Inputs**"))
    # generate table describing the input to the query
    cells.append(nbformat.v4.new_markdown_cell(gen_input_table(params, pybf_name)))

    cells.append(nbformat.v4.new_markdown_cell("###### **Invocation**"))
    parameters = question_data.get("parameters", [])
    param_str = ", ".join([f"{p['name']}={p['value']}" for p in parameters])
    if question_type == "diff":
        reference_snapshot = question_data["reference_snapshot"]["name"]
        # TODO: line wrapping?
        expression = f"bf.q.{pybf_name}({param_str}).answer(snapshot='{snapshot_name}',reference_snapshot='{reference_snapshot}')"
    else:
        expression = f"bf.q.{pybf_name}({param_str}).answer()"
    # execute the question and get the column metadata. Hack.
    column_metadata = eval(expression).metadata.column_metadata

    # Code cell to execute question
    cells.append(nbformat.v4.new_code_cell("result = {}.frame()".format(expression)))
    cells.append(nbformat.v4.new_markdown_cell("###### **Return Value**"))

    # generate table describing the output of the query
    cells.append(
        nbformat.v4.new_markdown_cell(gen_output_table(column_metadata, pybf_name))
    )

    generate_result_examination(cells, question_type)

    return cells


def generate_code_for_questions(
    question_list: List[Mapping[str, Any]],
    question_class_map: Mapping[str, QuestionMeta],
    session: Session,
) -> List[NotebookNode]:
    """Generate notebook cells for all questions in a single question category."""
    cells: List[NotebookNode] = []
    for question_data in question_list:
        cells.extend(
            generate_code_for_question(question_data, question_class_map, session)
        )
    return cells


def generate_notebook(
    category: Mapping[str, Any],
    question_class_map: Mapping[str, QuestionMeta],
    session: Session,
) -> NotebookNode:
    """Generate a notebook for a given question category."""
    # Create notebook object
    nb = nbformat.read(_BASE_Q_NOTEBOOK_FILE.open("r"), as_version=nbformat.NO_CONVERT)

    # Initialize list for cells that will be added.
    # Copying the cells from base notebook, so can just replace the value in the end
    cells: List[NotebookNode] = deepcopy(nb["cells"])
    description = "#### {}".format(category["description"])
    cells.append(nbformat.v4.new_markdown_cell(description))
    cells.append(nbformat.v4.new_markdown_cell(category["introduction"]))

    # Creates the list at the top of the page with hyperlinks to each question
    question_list = category["questions"]
    cells.append(generate_category_toc(question_list))

    # Creates the documentation for each question
    cells.extend(
        generate_code_for_questions(question_list, question_class_map, session)
    )

    # overwrite the cells with the fully populated list
    nb["cells"] = cells
    return nb


def execute_notebook(nb: NotebookNode, name: str) -> NotebookNode:
    """Executes a given notebook. Returns executed notebook.

    .. warning:: Will modify the passed in notebook.
    """
    logging.info("Executing Notebook for {} category of questions".format(name))

    # Execute the notebook and write to file
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": _DOC_DIR}})

    # Clear undesirable metadata from cells
    keep_metadata = {"nbsphinx"}
    for cell in nb.cells:
        meta = cell.get("metadata", {})
        cell["metadata"] = {k: v for k, v in meta.items() if k in keep_metadata}
    return nb


def write_notebook(nb: NotebookNode, path: Path) -> None:
    """Write a notebook to a given file path."""
    with path.open("w", encoding="utf-8") as f:
        nbformat.write(nb, f)


def generate_all_notebooks(
    question_categories: Mapping,
    question_class_map: Mapping[str, QuestionMeta],
    session: Session,
) -> None:
    """Generate (and write to disk) all question notebooks."""
    for category in progressbar.progressbar(question_categories["categories"]):
        nb = generate_notebook(category, question_class_map, session)
        name = category["name"]
        nb = execute_notebook(nb, name)
        write_notebook(nb, _EXEC_NOTEBOOK_DIR / f"{name}.ipynb")


def get_name_to_qclass(session: Session) -> Mapping[str, QuestionMeta]:
    """Return a map from question name to its pybf MetaClass"""
    # get a map from question name to class
    question_class_map = {
        name: member for name, member in inspect.getmembers(session.q, inspect.isclass)
    }
    if "__class__" in question_class_map:
        del question_class_map["__class__"]  # don't need this member
    return question_class_map


def init_snapshots(question_categories: Mapping, session: Session) -> None:
    """Initialize all snapshots needed for generating question notebooks."""
    snapshot_set: Set[Tuple[str, str]] = collect_snapshots(question_categories)

    logging.info("Initializing snapshots")
    for snapshot_config in progressbar.progressbar(snapshot_set):
        snapshot_path = _DOC_DIR / snapshot_config.path
        session.init_snapshot(
            str(snapshot_path), name=snapshot_config.name, overwrite=True
        )


def collect_snapshots(question_categories: Mapping) -> Set[Tuple[str, str]]:
    """Collect all snapshots needed for generating question notebooks.

    Returns each snapshot as tuple of (name, filepath)
    """
    # collect list of snapshots that need to be initialized
    ss = namedtuple("ss", ["name", "path"])
    snapshot_set: Set[Tuple[str, str]] = set()
    for category in question_categories["categories"]:
        for question in category["questions"]:
            snapshot = question.get("snapshot", _example_snapshot_config)
            snapshot_set.add(ss(**snapshot))

            if question.get("type", "basic") == "diff":
                snapshot = question.get("reference_snapshot", _example_snapshot_config)
                # Make a tuple so hashable and can put into a set
                snapshot_set.add(ss(**snapshot))
    return snapshot_set


def main() -> None:
    """Generate and write all notebooks for all question categories."""
    set_pandas_settings()
    progressbar.streams.wrap_stderr()
    logging.basicConfig(format="%(asctime)-15s %(message)s", level=logging.INFO)
    logging.getLogger("pybatfish").setLevel(logging.WARN)

    session = Session()
    question_class_map = get_name_to_qclass(session)

    # get the questions list and associated data to generate the docs
    questions_by_category = load_questions_yaml(_QUESTIONS_FILE)

    try:
        session.delete_network(NETWORK_NAME)
    except Exception:
        # No network exists, that's fine
        pass
    session.set_network(NETWORK_NAME)

    init_snapshots(questions_by_category, session)
    generate_all_notebooks(questions_by_category, question_class_map, session)
