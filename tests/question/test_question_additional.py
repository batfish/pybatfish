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

from __future__ import absolute_import, print_function

import pytest

from pybatfish.datamodel.primitives import VariableType
from pybatfish.question import question
from tests.conftest import COMPLETION_TYPES

# Tests for isSubRange

# These two tests will fail with original code due to typo in the code


def testInvalidSubRange():
    subRange = "100, 200"
    actualResult = question._isSubRange(subRange)
    expectMessage = "Invalid subRange: {}".format(subRange)
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidStartSubRange():
    subRange = "s100-200"
    actualResult = question._isSubRange(subRange)
    expectMessage = "Invalid subRange start: s100"
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidEndSubRange():
    subRange = "100-s200"
    actualResult = question._isSubRange(subRange)
    expectMessage = "Invalid subRange end: s200"
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testValidSubRange():
    subRange = "100-200"
    actualResult = question._isSubRange(subRange)
    assert actualResult[0]
    assert actualResult[1] is None


# Tests for isIp
def testInvalidIp():
    ip = "192.168.11"
    actualResult = question._isIp(ip)
    expectMessage = "Invalid ip string: '{}'".format(ip)
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidIpAddressWithIndicator():
    ip = "INVALID_IP(100)"
    actualResult = question._isIp(ip)
    expectMessage = "Invalid ip string: '{}'".format(ip)
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testValidIpAddressWithIndicator():
    ip = "INVALID_IP(100l)"
    actualResult = question._isIp(ip)
    assert actualResult[0]
    assert actualResult[1] is None


def testInvalidSegmentsIpAddress():
    ipAddress = "192.168.11.s"
    actualResult = question._isIp(ipAddress)
    expectMessage = "Ip segment is not a number: 's' in ip string: '192.168.11.s'"
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidSegmentRangeIpAddress():
    ipAddress = "192.168.11.256"
    actualResult = question._isIp(ipAddress)
    expectMessage = (
        "Ip segment is out of range 0-255: '256' in ip string: '192.168.11.256'"
    )
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidSegmentRangeIpAddress2():
    ipAddress = "192.168.11.-1"
    actualResult = question._isIp(ipAddress)
    expectMessage = (
        "Ip segment is out of range 0-255: '-1' in ip string: '192.168.11.-1'"
    )
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testValidIpAddress():
    ipAddress = "192.168.1.1"
    actualResult = question._isIp(ipAddress)
    assert actualResult[0]
    assert actualResult[1] is None


# Tests for _isPrefix
def testInvalidIpInPrefix():
    prefix = "192.168.1.s/100"
    actualResult = question._isPrefix(prefix)
    expectMessage = "Ip segment is not a number: 's' in ip string: '192.168.1.s'"
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidLengthInPrefix():
    prefix = "192.168.1.1/s"
    actualResult = question._isPrefix(prefix)
    expectMessage = "Prefix length must be an integer"
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testValidPrefix():
    prefix = "192.168.1.1/100"
    actualResult = question._isPrefix(prefix)
    assert actualResult[0]
    assert actualResult[1] is None


# Tests for _isPrefixRange
def testInvalidPrefixRangeInput():
    prefixRange = "192.168.1.s/100:100:100"
    actualResult = question._isPrefixRange(prefixRange)
    expectMessage = "Invalid PrefixRange string: '{}'".format(prefixRange)
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidPrefixInput():
    prefixRange = "192.168.1.s/100:100"
    actualResult = question._isPrefixRange(prefixRange)
    expectMessage = (
        "Invalid prefix string: '192.168.1.s/100' in prefix range string: '{}'".format(
            prefixRange
        )
    )
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidRangeInput():
    prefixRange = "192.168.1.1/100:100-s110"
    actualResult = question._isPrefixRange(prefixRange)
    expectMessage = "Invalid subRange end: s110"
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testValidPrefixRange():
    prefixRange = "192.168.1.1/100:100-110"
    actualResult = question._isPrefixRange(prefixRange)
    assert actualResult[0]
    assert actualResult[1] is None


# Tests for _isIpWildcard
def testInvalidIpWildcardWithColon():
    ipWildcard = "192.168.1.s:192.168.10.10:192"
    actualResult = question._isIpWildcard(ipWildcard)
    expectMessage = "Invalid IpWildcard string: '{}'".format(ipWildcard)
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidStartIpWildcardWithColon():
    ipWildcard = "192.168.1.s:192.168.1.1"
    actualResult = question._isIpWildcard(ipWildcard)
    expectMessage = "Invalid ip string: '192.168.1.s'"
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidEndIpWildcardWithColon():
    ipWildcard = "192.168.1.1:192.168.10.s"
    actualResult = question._isIpWildcard(ipWildcard)
    expectMessage = "Ip segment is not a number: 's' in ip string: '192.168.10.s'"
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testValidIpWildcardWithColon():
    ipWildcard = "192.168.1.1:192.168.10.10"
    actualResult = question._isIpWildcard(ipWildcard)
    assert actualResult[0]
    assert actualResult[1] is None


def testInvalidIpWildcardWithSlash():
    ipWildcard = "192.168.1.s/192.168.10.10/192"
    actualResult = question._isIpWildcard(ipWildcard)
    expectMessage = "Invalid IpWildcard string: '{}'".format(ipWildcard)
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidStartIpWildcardWithSlash():
    ipWildcard = "192.168.1.s/s"
    actualResult = question._isIpWildcard(ipWildcard)
    expectMessage = "Invalid ip string: '192.168.1.s'"
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testInvalidEndIpWildcardWithSlash():
    ipWildcard = "192.168.1.1/s"
    actualResult = question._isIpWildcard(ipWildcard)
    expectMessage = "Invalid prefix length: 's' in IpWildcard string: '{}'".format(
        ipWildcard
    )
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testValidIpWildcardWithSlash():
    ipWildcard = "192.168.1.1/100"
    actualResult = question._isIpWildcard(ipWildcard)
    assert actualResult[0]
    assert actualResult[1] is None


def testInvalidIpAddressIpWildcard():
    ipWildcard = "192.168.11.s"
    actualResult = question._isIpWildcard(ipWildcard)
    expectMessage = "Ip segment is not a number: 's' in ip string: '192.168.11.s'"
    assert not actualResult[0]
    assert expectMessage == actualResult[1]


def testValidIpAddressIpWildcard():
    ipWildcard = "192.168.11.1"
    actualResult = question._isIpWildcard(ipWildcard)
    assert actualResult[0]
    assert actualResult[1] is None


# Tests for validateType
def testInvalidBooleanValidateType():
    result = question._validate_type(1.5, "boolean")
    assert not result[0]


def testValidBooleanValidateType():
    result = question._validate_type(True, "boolean")
    assert result[0]


def testInvalidIntegerValidateType():
    result = question._validate_type(1.5, "integer")
    assert not result[0]


def testValidIntegerValidateType():
    result = question._validate_type(10, "integer")
    assert result[0]


def testInvalidComparatorValidateType():
    result = question._validate_type("<==", "comparator")
    expectMessage = (
        "'<==' is not a known comparator. Valid options are: '<, <=, ==, >=, >, !='"
    )
    assert not result[0]
    assert expectMessage == result[1]


def testValidComparatorValidateType():
    result = question._validate_type("<=", "comparator")
    assert result[0]


def testInvalidFloatValidateType():
    result = question._validate_type(10, "float")
    assert not result[0]


def testValidFloatValidateType():
    result = question._validate_type(10.0, "float")
    assert result[0]


def testInvalidDoubleValidateType():
    result = question._validate_type(10, "double")
    assert not result[0]


def testValidDoubleValidateType():
    result = question._validate_type(10.0, "double")
    assert result[0]


def testInvalidLongValidateType():
    result = question._validate_type(5.3, "long")
    assert not result[0]
    result = question._validate_type(2**64, "long")
    assert not result[0]


def testValidLongValidateType():
    result = question._validate_type(10, "long")
    assert result[0]
    result = question._validate_type(2**40, "long")
    assert result[0]


def testInvalidJavaRegexValidateType():
    result = question._validate_type(10, "javaRegex")
    expectMessage = "A Batfish javaRegex must be a string"
    assert not result[0]
    assert expectMessage == result[1]


def testInvalidNonDictionaryJsonPathValidateType():
    result = question._validate_type(10, "jsonPath")
    expectMessage = "Expected a jsonPath dictionary with elements 'path' (string) and optional 'suffix' (boolean)"
    assert not result[0]
    assert expectMessage == result[1]


def testInvalidDictionaryJsonPathValidateType():
    result = question._validate_type({"value": 10}, "jsonPath")
    expectMessage = "Missing 'path' element of jsonPath"
    assert not result[0]
    assert expectMessage == result[1]


def testPathNonStringJsonPathValidateType():
    result = question._validate_type({"path": 10}, "jsonPath")
    expectMessage = "'path' element of jsonPath dictionary should be a string"
    assert not result[0]
    assert expectMessage == result[1]


def testSuffixNonBooleanJsonPathValidateType():
    result = question._validate_type({"path": "I am path", "suffix": "hi"}, "jsonPath")
    expectMessage = "'suffix' element of jsonPath dictionary should be a boolean"
    assert not result[0]
    assert expectMessage == result[1]


def testValidJsonPathValidateType():
    result = question._validate_type({"path": "I am path", "suffix": True}, "jsonPath")
    assert result[0]
    assert result[1] is None


def testInvalidTypeSubRangeValidateType():
    result = question._validate_type(10.0, "subrange")
    expectMessage = "A Batfish subrange must either be a string or an integer"
    assert not result[0]
    assert expectMessage == result[1]


def testValidIntegerSubRangeValidateType():
    result = question._validate_type(10, "subrange")
    assert result[0]
    assert result[1] is None


def testNonStringProtocolValidateType():
    result = question._validate_type(10.0, "protocol")
    expectMessage = "A Batfish protocol must be a string"
    assert not result[0]
    assert expectMessage == result[1]


def testInvalidProtocolValidateType():
    result = question._validate_type("TCPP", "protocol")
    expectMessage = (
        "'TCPP' is not a valid protocols. Valid options are: 'dns, ssh, tcp, udp'"
    )
    assert not result[0]
    assert expectMessage == result[1]


def testValidProtocolValidateType():
    result = question._validate_type("TCP", "protocol")
    assert result[0]
    assert result[1] is None


def testNonStringIpProtocolValidateType():
    result = question._validate_type(10.0, "ipProtocol")
    expectMessage = "A Batfish ipProtocol must be a string"
    assert not result[0]
    assert expectMessage == result[1]


def testInvalidIntegerIpProtocolValidateType():
    result = question._validate_type("1000", "ipProtocol")
    expectMessage = "'1000' is not in valid ipProtocol range: 0-255"
    assert not result[0]
    assert expectMessage == result[1]


def testValidIntegerIpProtocolValidateType():
    result = question._validate_type("10", "ipProtocol")
    assert result[0]
    assert result[1] is None


def testInvalidCompletionTypes():
    # TODO: simplify to COMPLETION_TYPES after VariableType.BGP_ROUTE_STATUS_SPEC is moved
    for completion_type in set(COMPLETION_TYPES + [VariableType.BGP_ROUTE_STATUS_SPEC]):
        result = question._validate_type(5, completion_type)
        expectMessage = f"A Batfish {completion_type.value} must be a string"
        assert not result[0]
        assert result[1] == expectMessage


def testValidCompletionTypes():
    values = {
        VariableType.IP: "1.2.3.4",
        VariableType.PREFIX: "1.2.3.4/24",
        VariableType.PROTOCOL: "ssh",
    }
    # TODO: simplify to COMPLETION_TYPES after VariableType.BGP_ROUTE_STATUS_SPEC is moved
    for completion_type in set(COMPLETION_TYPES + [VariableType.BGP_ROUTE_STATUS_SPEC]):
        result = question._validate_type(
            values.get(completion_type, ".*"), completion_type
        )
        assert result[0]
        assert result[1] is None


if __name__ == "__main__":
    pytest.main()
