from pybatfish.datamodel.route import (
    BgpRoute,
    BgpRouteConstraints,
    BgpRouteDiff,
    _longspace_brc_converter,
    _string_list_brc_converter,
)


def testBgpRouteDeserialization():
    network = "0.0.0.0/0"
    asPath = [1, 2, 3]
    communities = [4, 5, 6]
    localPreference = 1
    metric = 2
    originType = "egp"
    originatorIp = "1.1.1.1"
    protocol = "bgp"

    dct = {
        "network": network,
        "asPath": asPath,
        "communities": communities,
        "localPreference": localPreference,
        "metric": metric,
        "originatorIp": originatorIp,
        "originType": originType,
        "protocol": protocol,
    }
    bgpRoute = BgpRoute.from_dict(dct)
    assert bgpRoute.network == network
    assert bgpRoute.communities == communities
    assert bgpRoute.localPreference == localPreference
    assert bgpRoute.metric == metric
    assert bgpRoute.originType == originType
    assert bgpRoute.originatorIp == originatorIp
    assert bgpRoute.protocol == protocol


def testBgpRouteSerialization():
    network = "0.0.0.0/0"
    asPath = [1, 2, 3]
    communities = [4, 5, 6]
    localPreference = 1
    metric = 2
    originType = "egp"
    originatorIp = "1.1.1.1"
    protocol = "bgp"

    bgpRoute = BgpRoute(
        network=network,
        asPath=asPath,
        communities=communities,
        localPreference=localPreference,
        metric=metric,
        originatorIp=originatorIp,
        originType=originType,
        protocol=protocol,
    )

    dct = bgpRoute.dict()

    assert dct["class"] == "org.batfish.datamodel.BgpRoute"
    assert dct["network"] == network
    assert dct["asPath"] == asPath
    assert dct["communities"] == communities
    assert dct["localPreference"] == localPreference
    assert dct["metric"] == metric
    assert dct["originatorIp"] == originatorIp
    assert dct["originType"] == originType
    assert dct["protocol"] == protocol


def test_bgp_route_str():
    bgp_route = BgpRoute(
        network="A",
        asPath=[1, 2],
        communities=[1, 2, 3],
        localPreference=4,
        metric=5,
        originatorIp="1.1.1.1",
        originType="egp",
        protocol="bgp",
        sourceProtocol="connected",
    )
    lines = bgp_route._repr_html_lines()
    assert lines == [
        "Network: A",
        "AS Path: [1, 2]",
        "Communities: [1, 2, 3]",
        "Local Preference: 4",
        "Metric: 5",
        "Originator IP: 1.1.1.1",
        "Origin Type: egp",
        "Protocol: bgp",
        "Source Protocol: connected",
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
