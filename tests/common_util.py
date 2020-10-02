# coding=utf-8
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
import os

import pytest
from decorator import decorator

import pybatfish
from pybatfish.client.session import Session


def _version_to_tuple(version):
    """Convert version string N(.N)* to a tuple of ints."""
    return tuple((int(i) for i in version.split(".")))


def _get_pybf_version():
    """
    Get version string for Pybatfish.

    Pybatfish version is pulled from pybf_version env var if set and non-empty, otherwise pulls from __version__ in pybatfish module.
    """
    pybf_version = os.environ.get("pybf_version")
    if pybf_version is None:
        pybf_version = pybatfish.__version__
    return pybf_version


def _version_less_than(version, min_version):
    """
    Check if specified version is less than the specified min version.

    Assumed dev versions start with a 0.
    """
    # Assume the dev version starts with a 0
    if version[0] != 0:
        return version < min_version
    # Dev version is considered newer than any version
    return False


def skip_old_version(bf_version, min_version):
    """Skip this pytest test if specified (or inferred) Pybf/Bf version is below supplied, minimum required version."""
    min_version_tuple = _version_to_tuple(min_version)
    if _version_less_than(_version_to_tuple(bf_version), min_version_tuple):
        pytest.skip("Batfish version too low ({} < {})".format(bf_version, min_version))
    pybf_version = _get_pybf_version()
    if _version_less_than(_version_to_tuple(pybf_version), min_version_tuple):
        pytest.skip(
            "Pybatfish version too low ({} < {})".format(pybf_version, min_version)
        )


def get_bf_version(session):
    """Get BF version."""
    # Use env var as version number if specified (get around some backends incorrectly having dev version number)
    return os.environ.get("bf_version", session._get_bf_version())


def requires_bf(version):
    """
    Decorator that will skip a test if the Batfish or Pybatfish version is older than the specified version.

    Bf version is pulled from bf_version env var if set and non-empty, otherwise pulls from the first session object passed into the test.
    Pybatfish version is pulled from pybf_version env var if set and non-empty, otherwise pulls from __version__ in pybatfish module.
    """

    # This outer decorator only accepts version string, not the actual
    # target function

    def function_decorator(func):
        # Inner 'decorator' accepts the target function

        def wrapper(func, *args, **kwargs):
            # Perform version validation and actually run the function
            bf_version = os.environ.get("bf_version")
            if not bf_version:
                for a in args:
                    if isinstance(a, Session):
                        bf_version = get_bf_version(a)
                        break
                for k in kwargs:
                    arg = kwargs[k]
                    if isinstance(arg, Session):
                        bf_version = get_bf_version(arg)
                        break
            if not bf_version:
                raise ValueError(
                    "Bad Batfish version.  Make sure either the bf_version env var is set or the decorated test accepts a session fixture."
                )
            skip_old_version(bf_version=bf_version, min_version=version)
            return func(*args, **kwargs)

        return decorator(wrapper, func)

    return function_decorator
