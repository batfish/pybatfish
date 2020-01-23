# coding: utf-8
import re
from typing import Optional

from inflection import dasherize, underscore

# Convert Java types to python types
_BASE_TYPES = {
    "integer": "int",
    "long": "int",
    "boolean": "bool",
    "string": "str",
    "double": "float",
}

# Convert input types (i.e., template variable types) to python types
_INPUT_TYPES = {
    "comparator": "str",
    "bgproute": "pybatfish.datamodel.route.BgpRoute",
    "edge": "pybatfish.datamodel.primitives.Edge",
    "interface": "pybatfish.datamodel.primitives.Interface",
    "ip": "str",
    "javaregex": "str",
    "headerconstraint": "pybatfish.datamodel.flow.HeaderConstraints",
    "node": "str",
    "pathconstraint": "pybatfish.datamodel.flow.PathConstraints",
    "prefix": "str",
    "structurename": "str",
    "vrf": "str",
}

# Convert output types (i.e., schema) to python types
_OUTPUT_TYPES = {
    "acltrace": "pybatfish.datamodel.acl.AclTrace",
    "acltraceevent": "pybatfish.datamodel.acl.AclTraceEvent",
    "bgproute": "pybatfish.datamodel.route.BgpRoute",
    "bgproutediffs": "pybatfish.datamodel.route.BgpRouteDiffs",
    "edge": "pybatfish.datamodel.primitives.Edge",
    "filelines": "pybatfish.datamodel.primitives.FileLines",
    "flow": "pybatfish.datamodel.flow.Flow",
    "flowtrace": "pybatfish.datamodel.flow.FlowTrace",
    "interface": "str",
    "ip": "str",
    "node": "str",
    "prefix": "str",
    "selfdescribing": "selfdescribing",
    "trace": "pybatfish.datamodel.flow.Trace",
    "tracetree": "pybatfish.datamodel.acl.TraceTree",
}

# Convert self-describing schemas to a python type (question-specific)
self_describing_map = {
    "bgpPeerConfiguration": "str",
    "bgpSessionCompatibility": "str",
    "bgpSessionStatus": "str",
    "namedStructures": "dict",
}


def convert_schema(value: str, usage: str, question_name: Optional[str] = None) -> str:
    """
    Converts the return values from question class into the appropriate type
    (as a link to the pybatfish datamodel or specifier description, if applicable)
    """

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
        slug = _INPUT_TYPES[value.lower()]
        if slug.startswith("pybatfish.datamodel"):
            text = slug.split(".")[-1]  # The class name
            return f"[{text}](../datamodel.rst#{slug})"
        else:
            return slug
    elif usage == "output":
        slug = _OUTPUT_TYPES[value.lower()]
        if slug.startswith("pybatfish.datamodel"):
            text = slug.split(".")[-1]  # The class name
            return f"[{text}](../datamodel.rst#{slug})"
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
