# coding: utf-8
import re
from typing import Optional

from inflection import camelize, dasherize, underscore

_BASE_TYPES = {
    "integer": "int",
    "long": "int",
    "boolean": "bool",
    "string": "str",
    "double": "float",
}

_INPUT_TYPES = {
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

_OUTPUT_TYPES = {
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


def convert_schema(
    input_value: str, usage: str, question_name: Optional[str] = None
) -> str:
    """
    Converts the return values from question class into the appropriate type
    (as a link to the pybatfish datamodel or specifier description, if applicable)
    """
    # deal plurality discrepancies
    value = replacement_map.get(
        camelize(input_value, uppercase_first_letter=False), input_value
    )

    if value.startswith("Set<"):
        inner = value[4:-1]  # strip prefix and suffix ">"
        return "Set of {}".format(convert_schema(inner, usage, question_name))
    elif value.startswith("List<"):
        inner = value[5:-1]  # strip prefix and suffix ">"
        return "List of {}".format(convert_schema(inner, usage, question_name))
    elif value.lower() in _BASE_TYPES:
        return _BASE_TYPES[value.lower()]
    elif value.endswith("Spec"):
        # specifiers follow a nice pattern, so no need for a manual map.
        # 1. convert camel case to a dashed version
        # 2. turn spec into specifier
        slug = re.sub(r"spec$", "specifier", dasherize(underscore(value)))
        return f"[{value}](../specifiers.md#{slug})"
    elif usage == "input":
        slug = _INPUT_TYPES.get(value.lower(), value)
        if slug.startswith("pybatfish.datamodel"):
            return f"[{value}](../datamodel.rst#{slug})"
        else:
            return slug
    elif usage == "output":
        slug = _OUTPUT_TYPES.get(value.lower(), value)
        if slug.startswith("pybatfish.datamodel"):
            return f"[{value}](../datamodel.rst#{slug})"
        elif slug.lower() == "selfdescribing":
            if question_name is None:
                raise ValueError(
                    "Converting selfdescribing schema requires a question name"
                )
            try:
                return self_describing_map[question_name]
            except KeyError:
                raise KeyError(
                    f"Error: unknown selfdescribing schema usage in question {question_name}"
                )
        else:
            return slug
    else:
        raise ValueError(
            f"Error: Unable to convert based on parameters - value: {value}, type {usage}, question {question_name}"
        )
