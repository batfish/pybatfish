import pytest

from pybatfish.datamodel.route import (
    BgpRoute,
    BgpRouteConstraints,
    BgpRouteDiff,
    NextHop,
    NextHopDiscard,
    NextHopInterface,
    NextHopIp,
    NextHopVrf,
    NextHopVtep,
    _longspace_brc_converter,
    _string_list_brc_converter,
)


def testBgpRouteDeserialization():
    network = "0.0.0.0/0"
    asPath = [1, 2, 3]
    communities = [4, 5, 6]
    localPreference = 1
    metric = 2
    nextHopIp = "2.2.2.2"
    originType = "egp"
    originatorIp = "1.1.1.1"
    protocol = "bgp"
    srcProtocol = "connected"
    tag = 23
    weight = 42

    dct = {
        "network": network,
        "asPath": asPath,
        "communities": communities,
        "localPreference": localPreference,
        "metric": metric,
        "nextHopIp": nextHopIp,
        "originatorIp": originatorIp,
        "originType": originType,
        "protocol": protocol,
        "srcProtocol": srcProtocol,
        "tag": tag,
        "weight": weight,
    }
    bgpRoute = BgpRoute.from_dict(dct)
    assert bgpRoute.network == network
    assert bgpRoute.asPath == asPath
    assert bgpRoute.communities == communities
    assert bgpRoute.localPreference == localPreference
    assert bgpRoute.metric == metric
    assert bgpRoute.nextHopIp == nextHopIp
    assert bgpRoute.originType == originType
    assert bgpRoute.originatorIp == originatorIp
    assert bgpRoute.protocol == protocol
    assert bgpRoute.sourceProtocol == srcProtocol
    assert bgpRoute.tag == tag
    assert bgpRoute.weight == weight


def testBgpRouteSerialization():
    network = "0.0.0.0/0"
    asPath = [1, 2, 3]
    communities = [4, 5, 6]
    localPreference = 1
    metric = 2
    nextHopIp = "2.2.2.2"
    originType = "egp"
    originatorIp = "1.1.1.1"
    protocol = "bgp"
    srcProtocol = "connected"
    tag = 23
    weight = 42

    bgpRoute = BgpRoute(
        network=network,
        asPath=asPath,
        communities=communities,
        localPreference=localPreference,
        metric=metric,
        nextHopIp=nextHopIp,
        originatorIp=originatorIp,
        originType=originType,
        protocol=protocol,
        sourceProtocol=srcProtocol,
        tag=tag,
        weight=weight,
    )

    dct = bgpRoute.dict()

    assert dct["class"] == "org.batfish.datamodel.questions.BgpRoute"
    assert dct["network"] == network
    assert dct["asPath"] == asPath
    assert dct["communities"] == communities
    assert dct["localPreference"] == localPreference
    assert dct["metric"] == metric
    assert dct["nextHopIp"] == nextHopIp
    assert dct["originatorIp"] == originatorIp
    assert dct["originType"] == originType
    assert dct["protocol"] == protocol
    assert dct["srcProtocol"] == srcProtocol
    assert dct["tag"] == tag
    assert dct["weight"] == weight


def test_bgp_route_str():
    bgp_route = BgpRoute(
        network="A",
        asPath=[1, 2],
        communities=[1, 2, 3],
        localPreference=4,
        metric=5,
        nextHopIp="2.2.2.2",
        originatorIp="1.1.1.1",
        originType="egp",
        protocol="bgp",
        sourceProtocol="connected",
        tag=23,
        weight=42,
    )
    lines = bgp_route._repr_html_lines()
    assert lines == [
        "Network: A",
        "AS Path: [1, 2]",
        "Communities: [1, 2, 3]",
        "Local Preference: 4",
        "Metric: 5",
        "Next Hop IP: 2.2.2.2",
        "Originator IP: 1.1.1.1",
        "Origin Type: egp",
        "Protocol: bgp",
        "Source Protocol: connected",
        "Tag: 23",
        "Weight: 42",
    ]


def testBgpRouteConstraintsDeserialization():
    prefix = ["1.2.3.4/5:6-7", "8.8.8.8:8/8-8"]
    complementPrefix = True
    localPreference = "1-2, 3-4, !5-6"
    med = "0-255, !50-55"
    communities = ["/.*/", "!/4[0-9]:2.+/"]
    asPath = ["/.*/", "40"]

    dct = {
        "prefix": prefix,
        "complementPrefix": complementPrefix,
        "localPreference": localPreference,
        "med": med,
        "communities": communities,
        "asPath": asPath,
    }
    bgpRouteConstraints = BgpRouteConstraints.from_dict(dct)
    assert bgpRouteConstraints.prefix == prefix
    assert bgpRouteConstraints.complementPrefix == complementPrefix
    assert bgpRouteConstraints.localPreference == localPreference
    assert bgpRouteConstraints.med == med
    assert bgpRouteConstraints.communities == communities
    assert bgpRouteConstraints.asPath == asPath


def testBgpRouteConstraintsConversions():

    prefix = "1.2.3.4/5:6-7"
    communities = ["20:30"]
    med = ["1-2", "3-4", "!5-6"]
    localPreference = []

    assert _string_list_brc_converter(prefix) == [prefix]
    assert _string_list_brc_converter(communities) == communities
    assert _longspace_brc_converter(med) == "1-2,3-4,!5-6"
    assert _longspace_brc_converter(localPreference) == ""


def testBgpRouteDiffDeserialization():
    name = "communities"
    oldValue = "old"
    newValue = "new"
    dct = {"fieldName": name, "oldValue": oldValue, "newValue": newValue}
    routeDiff = BgpRouteDiff.from_dict(dct)
    assert routeDiff.fieldName == name
    assert routeDiff.oldValue == oldValue
    assert routeDiff.newValue == newValue


def testBgpRouteDiffStr():
    diff1 = BgpRouteDiff(fieldName="nm", oldValue="old", newValue="new")
    diff2 = BgpRouteDiff(fieldName="localPreference", oldValue="old", newValue="new")
    assert diff1._repr_html_() == "Nm: old --> new"
    assert diff2._repr_html_() == "Local Preference: old --> new"


def testNextHopCannotInstantiate():
    with pytest.raises(TypeError):
        NextHop()


def testNextHopDeserializationInvalid():
    with pytest.raises(ValueError):
        NextHop.from_dict({"type": "foo"})
    with pytest.raises(ValueError):
        NextHop.from_dict({})


def testNextHopDiscardSerialization():
    assert NextHopDiscard().dict() == {"type": "discard"}


def testNextHopDiscardDeserialization():
    assert NextHop.from_dict({"type": "discard"}) == NextHopDiscard()
    assert NextHopDiscard.from_dict({"type": "discard"}) == NextHopDiscard()


def testNextHopDiscardStr():
    assert str(NextHopDiscard()) == "discard"


def testNextHopInterfaceSerialization():
    assert NextHopInterface("foo").dict() == {
        "type": "interface",
        "interface": "foo",
        "ip": None,
    }
    assert NextHopInterface("foo", "1.1.1.1").dict() == {
        "type": "interface",
        "interface": "foo",
        "ip": "1.1.1.1",
    }


def testNextHopInterfaceDeserialization():
    assert NextHop.from_dict(
        {"type": "interface", "interface": "foo"}
    ) == NextHopInterface("foo")
    assert NextHopInterface.from_dict(
        {"type": "interface", "interface": "foo"}
    ) == NextHopInterface("foo")
    assert NextHopInterface.from_dict(
        {"type": "interface", "interface": "foo", "ip": None}
    ) == NextHopInterface("foo")
    assert NextHopInterface.from_dict(
        {"type": "interface", "interface": "foo", "ip": "1.1.1.1"}
    ) == NextHopInterface("foo", "1.1.1.1")


def testNextHopInterfaceStr():
    assert str(NextHopInterface("foo")) == "interface foo"
    assert str(NextHopInterface("foo bar")) == 'interface "foo bar"'
    assert (
        str(NextHopInterface("foo bar", "1.1.1.1")) == 'interface "foo bar" ip 1.1.1.1'
    )


def testNextHopIpSerialization():
    assert NextHopIp("1.1.1.1").dict() == {"type": "ip", "ip": "1.1.1.1"}


def testNextHopIpDeserialization():
    assert NextHop.from_dict({"type": "ip", "ip": "1.1.1.1"}) == NextHopIp("1.1.1.1")
    assert NextHopIp.from_dict({"type": "ip", "ip": "1.1.1.1"}) == NextHopIp("1.1.1.1")


def testNextHopIpStr():
    assert str(NextHopIp("1.1.1.1")) == "ip 1.1.1.1"


def testNextHopVrfSerialization():
    assert NextHopVrf("foo").dict() == {"type": "vrf", "vrf": "foo"}


def testNextHopVrfDeserialization():
    assert NextHop.from_dict({"type": "vrf", "vrf": "foo"}) == NextHopVrf("foo")
    assert NextHopVrf.from_dict({"type": "vrf", "vrf": "foo"}) == NextHopVrf("foo")


def testNextHopVrfStr():
    assert str(NextHopVrf("foo")) == "vrf foo"
    assert str(NextHopVrf("foo bar")) == 'vrf "foo bar"'


def testNextHopVtepSerialization():
    assert NextHopVtep(5, "1.1.1.1").dict() == {
        "type": "vtep",
        "vni": 5,
        "vtep": "1.1.1.1",
    }


def testNextHopVtepDeserialization():
    assert NextHop.from_dict(
        {"type": "vtep", "vni": 5, "vtep": "1.1.1.1"}
    ) == NextHopVtep(5, "1.1.1.1")
    assert NextHopVtep.from_dict(
        {"type": "vtep", "vni": 5, "vtep": "1.1.1.1"}
    ) == NextHopVtep(5, "1.1.1.1")


def testNextHopVtepStr():
    assert str(NextHopVtep(5, "1.1.1.1")) == "vni 5 vtep 1.1.1.1"
