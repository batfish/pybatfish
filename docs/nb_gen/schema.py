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
    "bgprouteconstraints": "pybatfish.datamodel.route.BgpRouteConstraints",
    "bgproutes": "List[pybatfish.datamodel.route.BgpRoute]",
    "bgpsessionproperties": "pybatfish.datamodel.route.BgpSessionProperties",
    "edge": "pybatfish.datamodel.primitives.Edge",
    "integerspace": "str",
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
    "interface": "pybatfish.datamodel.primitives.Interface",
    "ip": "str",
    "nexthop": "pybatfish.datamodel.route.NextHop",
    "node": "str",
    "prefix": "str",
    "selfdescribing": "selfdescribing",  # not a real python type; handled separately in code
    "trace": "pybatfish.datamodel.flow.Trace",
    "tracetree": "pybatfish.datamodel.acl.TraceTree",
}

# Normalizes specifier types to how they are documented in Markdown ಠ_ಠ
# The right side of this map must be camel-cased so that link creation works correctly (by downstream code)
_SPECIFIER_CONVERSIONS = {"interfacesspec": "interfaceSpec", "ipspacespec": "ipSpec"}

# Convert self-describing schemas to a python type (question-specific)
_SELF_DESCRIBING_CONVERSIONS = {
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
    allowed_usages = ["input", "output", "python"]
    if usage not in allowed_usages:
        raise ValueError(
            f"Invalid conversion type: {usage}, expected one of: {allowed_usages}"
        )

    if value.startswith("Set<"):
        inner = value[4:-1]  # strip prefix and suffix ">"
        return "Set of {}".format(convert_schema(inner, usage, question_name))
    elif value.startswith("List<") or value.startswith("List["):
        inner = value[5:-1]  # strip prefix and suffix ">"
        return "List of {}".format(convert_schema(inner, usage, question_name))
    elif value.lower() in _BASE_TYPES:
        return _BASE_TYPES[value.lower()]
    elif value.endswith("Spec"):
        # specifiers follow a nice pattern. Almost.
        # 1. Handle special cases
        # 2. convert camel case to a dashed version
        # 3. turn "spec" into "specifier"
        value = _SPECIFIER_CONVERSIONS.get(value.lower(), value)
        slug = re.sub(r"spec$", "specifier", dasherize(underscore(value)))
        text = value[:1].capitalize() + value[1:]
        return f"[{text}](../specifiers.md#{slug})"
    elif value.startswith("pybatfish.datamodel"):
        text = value.split(".")[-1]  # The class name
        return f"[{text}](../datamodel.rst#{value})"
    elif value.lower() == "selfdescribing":
        if question_name is None:
            raise ValueError(
                "Converting selfdescribing schema requires a question name"
            )
        try:
            return _SELF_DESCRIBING_CONVERSIONS[question_name]
        except KeyError:
            raise KeyError(
                f"Error: unknown selfdescribing schema usage in question {question_name}"
            )
    elif usage == "python":  # simple python type
        return value
    elif usage == "input":
        slug = _INPUT_TYPES[value.lower()]
        return convert_schema(slug, "python", question_name)
    elif usage == "output":
        slug = _OUTPUT_TYPES[value.lower()]
        return convert_schema(slug, "python", question_name)
    else:
        raise ValueError(
            f"Error: Unable to convert based on parameters - value: {value}, type {usage}, question {question_name}"
        )
