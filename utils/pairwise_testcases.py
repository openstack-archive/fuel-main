import metacomm.combinatorics.all_pairs2

all_pairs = metacomm.combinatorics.all_pairs2.all_pairs2

parameters = [
    #("os", ["CentOS", "RedHat", "Ubuntu"]),
    ("mode", ["simple", "HA"]),
    ("controller", [1, 3]),
    ("compute", [1, 2]),
    ("cinder", [1, 2, 0]),
    ("ceph", [2, 3, 0]),
    ("network", ["nova flat", "nova vlan", "neutron GRE", "neutron VLAN"]),
    ("tagging", ["yes", "no"]),
    ("storage volume", ["default", "ceph"]),
    ("storage images", ["default", "ceph"]),
    ("savanna", ["yes", "no"]),
    ("murano", ["yes", "no"]),
    ("ceilometer", ["yes", "no"])
]


def is_valid_combination(values, names):
    dictionary = dict(zip(names, values))

    """
    Should return True if combination is valid and False otherwise.

    Dictionary that is passed here can be incomplete.
    To prevent search for unnecessary items filtering function
    is executed with found subset of data to validate it.
    """

    rules = [
        lambda d: "RedHat" == d["os"] and "ceph" == d["storage volume"]
        , lambda d: "RedHat" == d["os"] and "ceph" == d["storage images"]
        , lambda d: "RedHat" == d["os"] and "yes" == d["savanna"]
        , lambda d: "RedHat" == d["os"] and "yes" == d["murano"]
        , lambda d: "RedHat" == d["os"] and "neutron GRE" == d["network"]
        , lambda d: "RedHat" == d["os"] and "neutron VLAN" == d["network"]
        , lambda d: d["cinder"] > 0 and d["storage volume"] == "default"
        , lambda d: d["ceph"] > 0 and d["storage volume"] == "default" and d["storage images"] == "default"
    ]

    for rule in rules:
        try:
            if rule(dictionary):
                return False
        except KeyError:
            pass

    return True


pairwise = all_pairs(
    [x[1] for x in parameters]
    , filter_func=lambda values: is_valid_combination(values, [x[0] for x in
                                                               parameters])
)

for i, v in enumerate(pairwise):
    print "%i:\t%s" % (i, v)
