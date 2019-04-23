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
from os.path import abspath, dirname, realpath

from pytest import fixture

from pybatfish.client.capirca import create_reference_book
from pybatfish.client.commands import (bf_delete_network, bf_get_reference_book,
                                       bf_put_reference_book, bf_set_network)

_this_dir = abspath(dirname(realpath(__file__)))


@fixture()
def network():
    name = bf_set_network()
    yield name
    # cleanup
    bf_delete_network(name)


def test_create_reference_book(network):
    book = create_reference_book(os.path.join(_this_dir, 'capirca'))
    bf_put_reference_book(book)

    getbook = bf_get_reference_book('capirca')
    # TODO: can this just be book equality? Right now, books are implemented
    #  with contents that are lists, and converting to set broke a bunch of
    #  tests that expect those lists to be indexable.
    assert getbook.name == book.name
    assert (set(g.name for g in getbook.addressGroups) ==
            set(g.name for g in book.addressGroups))
