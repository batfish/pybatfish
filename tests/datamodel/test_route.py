from pybatfish.datamodel.route import BgpRoute, BgpRouteDiff


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
    diff = BgpRouteDiff(fieldName="nm", oldValue="old", newValue="new")
    assert diff._repr_html_() == "nm: old -> new"
