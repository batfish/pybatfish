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
import pytest
import six
from pandas import DataFrame

from pybatfish.client.asserts import (_raise_common, assert_filter_denies,
                                      assert_filter_permits)
from pybatfish.datamodel import HeaderConstraints
from pybatfish.datamodel.answer import TableAnswer
from pybatfish.exception import (BatfishAssertException,
                                 BatfishAssertWarning)
from pybatfish.question import bfq
from pybatfish.question.question import QuestionBase

if six.PY3:
    from unittest.mock import patch
else:
    from mock import patch


def test_raise_common_default():
    with pytest.raises(BatfishAssertException) as e:
        _raise_common("foobar")
    assert "foobar" in str(e.value)

    with pytest.raises(BatfishAssertException) as e:
        _raise_common("foobaragain", False)
    assert "foobaragain" in str(e.value)


def test_raise_common_warn():
    with pytest.warns(BatfishAssertWarning):
        result = _raise_common("foobar", True)
    assert not result


class MockTableAnswer(TableAnswer):
    def __init__(self, frame_to_use=DataFrame()):
        self._frame = frame_to_use

    def frame(self):
        return self._frame


class MockQuestion(QuestionBase):
    def __init__(self, answer=None):
        self._answer = answer if answer is not None else MockTableAnswer()

    def answer(self, **kwargs):
        return self._answer


def test_filter_permits():
    headers = HeaderConstraints(srcIps='1.1.1.1')
    with patch.object(bfq, 'searchFilters', create=True) as mock_search_filters:
        # Test success
        mock_search_filters.return_value = MockQuestion()
        assert_filter_permits('filter', headers)
        mock_search_filters.assert_called_with(filters='filter',
                                               headers=headers,
                                               action='deny')
        # Test failure; also test that startLocation is passed through
        mock_df = DataFrame.from_records([{'Flow': 'found', 'More': 'data'}])
        mock_search_filters.return_value = MockQuestion(
            MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_filter_permits('filter', headers, startLocation='Ethernet1')
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        mock_search_filters.assert_called_with(filters='filter',
                                               headers=headers,
                                               startLocation='Ethernet1',
                                               action='deny')


def test_filter_denies():
    headers = HeaderConstraints(srcIps='1.1.1.1')
    with patch.object(bfq, 'searchFilters', create=True) as mock_search_filters:
        # Test success
        mock_search_filters.return_value = MockQuestion()
        assert_filter_denies('filter', headers)
        mock_search_filters.assert_called_with(filters='filter',
                                               headers=headers,
                                               action='permit')
        # Test failure; also test that startLocation is passed through
        mock_df = DataFrame.from_records([{'Flow': 'found', 'More': 'data'}])
        mock_search_filters.return_value = MockQuestion(
            MockTableAnswer(mock_df))
        with pytest.raises(BatfishAssertException) as excinfo:
            assert_filter_denies('filter', headers, startLocation='Ethernet1')
        # Ensure found answer is printed
        assert mock_df.to_string() in str(excinfo.value)
        mock_search_filters.assert_called_with(filters='filter',
                                               headers=headers,
                                               startLocation='Ethernet1',
                                               action='permit')
