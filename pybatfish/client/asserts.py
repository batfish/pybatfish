# coding utf-8
#   Copyright 2018 The Batfish Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Utility assert functions for writing batfish tests.

All `assert_*` methods will raise an
:py:class:`~pybatfish.util.exception.BatfishAssertException` if the assertion
fails.
"""

import operator
from typing import Any, Dict, Iterable  # noqa: F401
import warnings

from deepdiff import DeepDiff

from pybatfish.datamodel.answer import Answer  # noqa: F401
from pybatfish.exception import (BatfishAssertException,
                                 BatfishAssertWarning)

__all__ = ['assert_dict_match',
           'assert_has_no_route',
           'assert_has_route',
           'assert_num_results',
           'assert_zero_results',
           ]


def assert_zero_results(answer, soft=False):
    # type: (Answer, bool) -> bool
    """Assert no results were returned.

    :param answer: Batfish answer
    :type answer: :py:class:`~pybatfish.datamodel.answer.Answer`
    :param soft: whether this assertion is soft (i.e., generates a warning but
        not a failure)
    :type soft: bool
    """
    return assert_num_results(answer, 0, soft)


def assert_num_results(answer, num, soft=False):
    # type: (Answer, int, bool) -> bool
    """Assert an exact number of results were returned.

    :param answer: Batfish answer
    :type answer: :py:class:`~pybatfish.datamodel.answer.Answer`
    :param num: expected number of results
    :type num: int
    :param soft: whether this assertion is soft (i.e., generates a warning but
        not a failure)
    :type soft: bool
    """
    __tracebackhide__ = operator.methodcaller("errisinstance",
                                              BatfishAssertException)
    actual = answer['summary']['numResults']
    if not actual == num:
        err_text = "Expected {} results, found: {}\nFull answer:\n{}".format(
            num, actual, answer)
        return _raise_common(err_text, soft)
    return True


def _subdict(d, keys):
    # type: (Dict, Iterable[str]) -> Dict[str, Any]
    """Helper function that retrieves a subset of a dictionary given some keys."""
    return {k: d.get(k) for k in keys}


def _is_dict_match(actual, expected):
    # type: (Dict, Dict) -> bool
    """Matches two dictionaries. `expected` can be a subset of `actual`."""
    diff = DeepDiff(_subdict(actual, expected.keys()), expected,
                    ignore_order=True, verbose_level=0, view='text')
    return not diff


def _raise_common(err_text, soft=False):
    # type: (str, bool) -> bool
    """Utility function for soft/hard exception raising."""
    if soft:
        warnings.warn(err_text, category=BatfishAssertWarning)
        return False
    else:
        raise BatfishAssertException(err_text)


def assert_dict_match(actual, expected, soft=False):
    # type: (Dict, Dict, bool) -> bool
    """Assert that two dictionaries are equal. `expected` can be a subset of `actual`.

    :param actual: the value tested.
    :param expected: the expected value of a dictionary
    :param soft: whether this assertion is soft (i.e., generates a warning but
        not a failure)
    """
    __tracebackhide__ = operator.methodcaller("errisinstance",
                                              BatfishAssertException)
    diff = DeepDiff(_subdict(actual, expected.keys()), expected,
                    ignore_order=True, verbose_level=0, view='text')
    if diff:
        err_text = "Unexpected differences found:\n{}".format(diff)
        return _raise_common(err_text, soft)
    return True


# TODO: converge on representation of routes. (Blocked on backend batfish).
# TODO: allow this to be role-based. (Again, backend support).
def assert_has_route(routes, expected_route, node, vrf='default', soft=False):
    """Assert that a particular route is present.

    :param routes: All routes returned by the Batfish routes question.
    :param expected_route: A dictionary describing route to match.
    :param node: node hostname on which to look for a route.
    :param vrf: VRF name where the route should be present. Default is `default`.
    :param soft: whether this assertion is soft (i.e., generates a warning but
        not a failure)
    :type soft: bool
    """
    __tracebackhide__ = operator.methodcaller("errisinstance",
                                              BatfishAssertException)
    try:
        d = routes[node]
    except KeyError:
        raise BatfishAssertException("No node: {}".format(node))

    try:
        d = d[vrf]
    except KeyError:
        raise BatfishAssertException("No VRF: {} on node {}".format(vrf, node))

    if not any(_is_dict_match(actual_route, expected_route)
               for actual_route in d):
        err_text = "No route matches for {} on node {}, VRF {}".format(
            expected_route, node, vrf)
        return _raise_common(err_text, soft)
    return True


def assert_has_no_route(routes, expected_route, node, vrf='default',
                        soft=False):
    """Assert that a particular route is **NOT** present.

    .. note:: If a node or VRF is missing in the route answer the assertion
    will NOT fail, but a warning will be generated.

    :param routes: All routes returned by the Batfish routes question.
    :param expected_route: A dictionary describing route to match.
    :param node: node hostname on which to look for expected route.
    :param vrf: VRF name to check. Default is `default`.
    :param soft: whether this assertion is soft (i.e., generates a warning but
        not a failure)
    :type soft: bool
    """
    __tracebackhide__ = operator.methodcaller("errisinstance",
                                              BatfishAssertException)
    try:
        d = routes[node]
    except KeyError:
        warnings.warn("No node: {}".format(node), category=BatfishAssertWarning)
        return True

    try:
        d = d[vrf]
    except KeyError:
        warnings.warn("No VRF: {} on node {}".format(vrf, node),
                      category=BatfishAssertWarning)
        return True

    all_matches = [route for route in d
                   if _is_dict_match(route, expected_route)]
    if all_matches:
        err_text = "Found route(s) that match, "
        "when none were expected:\n{}".format(
            all_matches)
        return _raise_common(err_text, soft)
    return True
