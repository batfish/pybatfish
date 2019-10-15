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
import pytest

from pybatfish.datamodel import ListWrapper


def test_list_wrapper_is_hashable():
    key = ListWrapper([1, 2, 3])
    val = ListWrapper([4, 5, 6])
    d = {key: val}
    assert d[key] == val


def test_list_wrapper_is_immutable():
    alist = ListWrapper([1, 2, 3])
    with pytest.raises(TypeError):
        alist[1] = 5


if __name__ == "__main__":
    pytest.main()
