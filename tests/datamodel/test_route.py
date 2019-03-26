from pybatfish.datamodel.route import BgpRoute, BgpRouteDiff


def testBgpRouteDeserialization():
    network = '0.0.0.0/0'
    asPath = [1, 2, 3]
    communities = [4, 5, 6]
    localPreference = 1
    metric = 2
    originType = 'egp'
    originatorIp = '1.1.1.1'
    protocol = 'bgp'

    dct = {
        'network': network,
        'asPath': asPath,
        'communities': communities,
        'localPreference': localPreference,
        'metric': metric,
        'originType': originType,
        'originatorIp': originatorIp,
        'protocol': protocol
    }
    bgpRoute = BgpRoute.from_dict(dct)
    assert bgpRoute.network == network
    assert bgpRoute.communities == communities
    assert bgpRoute.localPreference == localPreference
    assert bgpRoute.metric == metric
    assert bgpRoute.originType == originType
    assert bgpRoute.originatorIp == originatorIp
    assert bgpRoute.protocol == protocol


def testBgpRouteStr():
    bgpRoute = BgpRoute(
        network="A",
        asPath=[1, 2],
        communities=[1, 2, 3],
        localPreference=4,
        metric=5,
        originatorIp='1.1.1.1',
        originType='egp',
        protocol='bgp'
    )
    lines = bgpRoute._repr_html_lines()
    assert len(lines) == 8
    assert lines[0] == "Network: A"
    assert lines[1] == "AS Path: [1, 2]"
    assert lines[2] == "Communities: [1, 2, 3]"
    assert lines[3] == "Local Preference: 4"
    assert lines[4] == "Metric: 5"
    assert lines[5] == "Originator IP: 1.1.1.1"
    assert lines[6] == "Origin Type: egp"
    assert lines[7] == "Protocol: bgp"


def testBgpRouteDiffDeserialization():
    name = 'communities'
    oldValue = 'old'
    newValue = 'new'
    dct = {
        'fieldName': name,
        'oldValue': oldValue,
        'newValue': newValue,
    }
    routeDiff = BgpRouteDiff.from_dict(dct)
    assert routeDiff.fieldName == name
    assert routeDiff.oldValue == oldValue
    assert routeDiff.newValue == newValue


def testBgpRouteDiffStr():
    diff = BgpRouteDiff(fieldName='nm', oldValue='old', newValue='new')
    assert diff._repr_html_() == "nm: old -> new"
