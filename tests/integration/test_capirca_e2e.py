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

from pybatfish.client.capirca import create_reference_book, init_snapshot_from_acl
from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints

_this_dir = abspath(dirname(realpath(__file__)))


@fixture(scope="module")
def bf() -> Session:
    s = Session()
    return s


@fixture(scope="module")
def network(bf):
    name = bf.set_network()
    yield name
    # cleanup
    bf.delete_network(name)


def test_create_reference_book(bf, network):
    book = create_reference_book(os.path.join(_this_dir, "capirca", "defs"))
    bf.put_reference_book(book)

    getbook = bf.get_reference_book("capirca")
    # TODO: can this just be book equality? Right now, books are implemented
    #  with contents that are lists, and converting to set broke a bunch of
    #  tests that expect those lists to be indexable.
    assert getbook.name == book.name
    assert set(g.name for g in getbook.addressGroups) == set(
        g.name for g in book.addressGroups
    )


def test_init_snapshot_from_acl(bf: Session, network: str) -> None:
    defs = os.path.join(_this_dir, "capirca", "defs")
    pol = os.path.join(_this_dir, "capirca", "test.pol")
    ss = init_snapshot_from_acl(bf, pol, defs, platform="cisco", filename="some_cfg")

    ssh = HeaderConstraints(applications="ssh")
    dns = HeaderConstraints(applications="dns")
    http = HeaderConstraints(applications="http")

    bf.asserts.assert_filter_permits("some_acl", ssh, snapshot=ss)
    bf.asserts.assert_filter_permits("some_acl", dns, snapshot=ss)
    bf.asserts.assert_filter_denies("some_acl", http, snapshot=ss)
