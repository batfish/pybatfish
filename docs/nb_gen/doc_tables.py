# coding: utf-8
import inspect
from typing import Any, List, Tuple

from pybatfish.datamodel.answer.table import ColumnMetadata
from pybatfish.question.question import QuestionMeta

from .schema import convert_schema


def gen_output_table(col_data: List[ColumnMetadata], question_name: str) -> str:
    """
    Converts the return values from answer's column metadata into a markdown table
    """

    return "\n".join(get_output_table_lines(col_data, question_name))


def get_output_table_lines(
    col_data: List[ColumnMetadata], question_name: str
) -> List[str]:
    table_lines = ["Name | Description | Type", "--- | --- | ---"]
    for col in col_data:
        schema_type = convert_schema(col.schema, "output", question_name)
        table_lines.append(f"{col.name} | {col.description} | {schema_type}")
    return table_lines


def gen_input_table(parameters: List[Tuple[str, Any]], question_name: str) -> str:
    """
    Converts the input parameters from question class into a markdown table
    """
    if not parameters:
        return ""

    return "\n".join(get_input_table_lines(parameters, question_name))


def get_input_table_lines(
    parameters: List[Tuple[str, Any]], question_name: str
) -> List[str]:
    table_lines = [
        "Name | Description | Type | Optional | Default Value",
        "--- | --- | --- | --- | --- ",
    ]
    for name, param in parameters:
        desc = param["description"]
        schema_type = convert_schema(param["type"], "input", question_name)
        optional = param.get("optional", False)
        default_value = param.get("value", "")
        # Optional == true in the question template means backend can receive null as input.
        # In documentation we only care if user has to set it, so if a default value is present,
        # we call that optional
        if default_value:
            optional = True

        table_lines.append(
            f"{name} | {desc} | {schema_type} | {optional} | {default_value}"
        )
    return table_lines


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
