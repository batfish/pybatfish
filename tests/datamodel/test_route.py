from pybatfish.datamodel.route import BgpRoute, BgpRouteDiff


def testBgpRouteDeserialization():
    network = '0.0.0.0/0'
    asPath = [1, 2, 3]
    communities = [4, 5, 6]
    localPreference = 1
    metric = 2
    dct = {
        'network': network,
        'asPath': asPath,
        'communities': communities,
        'localPreference': localPreference,
        'metric': metric,
    }
    bgpRoute = BgpRoute.from_dict(dct)
    assert bgpRoute.network == network
    assert bgpRoute.communities == communities
    assert bgpRoute.localPreference == localPreference
    assert bgpRoute.metric == metric


def testBgpRouteStr():
    bgpRoute = BgpRoute(
        network="A",
        asPath=[1, 2],
        communities=[1, 2, 3],
        localPreference=4,
        metric=5)
    assert bgpRoute._repr_html_lines() == [
        "Network: A",
        "AS Path: [1, 2]",
        "Communities: [1, 2, 3]",
        "Local Preference: 4",
        "Metric: 5"
    ]


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
    assert str(diff) == "nm: old -> new"
