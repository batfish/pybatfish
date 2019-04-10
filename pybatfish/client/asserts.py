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
"""Utility assert functions for writing network tests (or policies).

All `assert_*` methods will raise an
:py:class:`~pybatfish.util.exception.BatfishAssertException` if the assertion
fails.
"""

import operator
import warnings
from typing import (Any, Dict, Iterable, Optional, TYPE_CHECKING,  # noqa: F401
                    Union)

from deepdiff import DeepDiff
from pandas import DataFrame

from pybatfish.datamodel import HeaderConstraints  # noqa: F401
from pybatfish.datamodel.answer import Answer, TableAnswer
from pybatfish.exception import (BatfishAssertException,
                                 BatfishAssertWarning, BatfishException)
from pybatfish.question import bfq

if TYPE_CHECKING:
    from pybatfish.client.session import Session

__all__ = [
    'assert_dict_match',
    'assert_filter_denies',
    'assert_filter_permits',
    'assert_has_no_route',
    'assert_has_route',
    'assert_num_results',
    'assert_zero_results',
]


def assert_zero_results(answer, soft=False):
    # type: (Union[Answer, TableAnswer, DataFrame], bool) -> bool
    """Assert no results were returned.

    :param answer: Batfish answer or DataFrame
    :param soft: whether this assertion is soft (i.e., generates a warning but
        not a failure)
    :type soft: bool
    """
    return assert_num_results(answer, 0, soft)


def assert_num_results(answer, num, soft=False):
    # type: (Union[Answer, TableAnswer, DataFrame], int, bool) -> bool
    """Assert an exact number of results were returned.

    :param answer: Batfish answer or DataFrame
    :param num: expected number of results
    :type num: int
    :param soft: whether this assertion is soft (i.e., generates a warning but
        not a failure)
    :type soft: bool
    """
    __tracebackhide__ = operator.methodcaller("errisinstance",
                                              BatfishAssertException)
    if isinstance(answer, DataFrame):
        actual = len(answer)
    elif isinstance(answer, TableAnswer):
        actual = len(answer.frame())
    elif isinstance(answer, Answer):
        actual = answer['summary']['numResults']
    else:
        raise TypeError("Unrecognized answer type")
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
    __tracebackhide__ = operator.methodcaller("errisinstance",
                                              BatfishAssertException)
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


def assert_filter_permits(filter_name, headers, startLocation=None, soft=False,
                          session=None):
    # type: (str, HeaderConstraints, str, bool, Optional[Session]) -> bool
    """
    Check if a named ACL permits a specified set of flows.

    :param filter_name: the name of ACL to check
    :param headers: :py:class:`~pybatfish.datamodel.flow.HeaderConstraints`
    :param startLocation: LocationSpec indicating where a flow starts
    :param soft: whether this assertion is soft (i.e., generates a warning but
        not a failure)
    :param session: Batfish session to use for the assertion
    :return: True if the assertion passes
    """
    __tracebackhide__ = operator.methodcaller("errisinstance",
                                              BatfishAssertException)

    kwargs = dict(filters=filter_name, headers=headers, action="deny")
    if startLocation is not None:
        kwargs.update(startLocation=startLocation)

    df = _get_question_object(session, 'searchFilters').searchFilters(
        **kwargs).answer().frame()  # type: ignore
    if len(df) > 0:
        return _raise_common(
            "Found a flow that was denied, when expected to be permitted\n{}".format(
                df.to_string()), soft)
    return True


def assert_filter_denies(filter_name, headers, startLocation=None, soft=False,
                         session=None):
    # type: (str, HeaderConstraints, str, bool, Optional[Session]) -> bool
    """
    Check if a named ACL denies a specified set of flows.

    :param filter_name: the name of ACL to check
    :param headers: :py:class:`~pybatfish.datamodel.flow.HeaderConstraints`
    :param startLocation: LocationSpec indicating where a flow starts
    :param soft: whether this assertion is soft (i.e., generates a warning but
        not a failure)
    :param session: Batfish session to use for the assertion
    :return: True if the assertion passes
    """
    __tracebackhide__ = operator.methodcaller("errisinstance",
                                              BatfishAssertException)

    kwargs = dict(filters=filter_name, headers=headers, action="permit")
    if startLocation is not None:
        kwargs.update(startLocation=startLocation)

    df = _get_question_object(session, 'searchFilters').searchFilters(
        **kwargs).answer().frame()  # type: ignore
    if len(df) > 0:
        return _raise_common(
            "Found a flow that was permitted, when expected to be denied\n{}".format(
                df.to_string()), soft)
    return True


def _get_question_object(session, name):
    """
    Get the question object for the specified session, containing the specified question name.

    Falls back to bfq if it contains the question and specified session does not.
    """
    # If no session was specified or it doesn't have the specified question
    # (e.g. questions were loaded with load_questions()), use bfq for reverse
    # compatibility
    if session and hasattr(session.q, name):
        return session.q
    elif hasattr(bfq, name):
        return bfq
    else:
        raise BatfishException('{} question was not found'.format(name))
