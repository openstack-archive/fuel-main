# -*- coding: utf-8 -*-

import web
from sqlalchemy.sql import not_
from netaddr import IPSet, IPNetwork, iter_iprange

from nailgun.db import orm
from nailgun.task import errors
from nailgun.settings import settings
from nailgun.api.models import Node, IPAddr, Cluster
from nailgun.api.models import Network, NetworkGroup


def is_ip_used(ip):
    used = orm().query(IPAddr).filter_by(ip_addr=ip).first()
    return (used is not None)


def get_free_ip_from_range(iterable, num=1):
    from_range = set(iterable)
    diff = from_range - set(
        [i.ip_addr for i in orm().query(IPAddr).
         filter(IPAddr.ip_addr.in_(from_range))]
    )
    try:
        return [diff.pop() for i in xrange(num)]
    except KeyError:
        raise Exception(
            "Not enough free ip addresses in ip pool"
        )


def assign_admin_ips(node_id, num=1):
    node_admin_ips = orm().query(IPAddr).\
        filter_by(admin=True).filter_by(node=node_id).all()

    if not node_admin_ips or len(node_admin_ips) < num:
        free_ips = get_free_ip_from_range(
            [str(i) for i in iter_iprange(
                settings.ADMIN_NETWORK['first'],
                settings.ADMIN_NETWORK['last']
            )],
            num=num - len(node_admin_ips)
        )
        for ip in free_ips:
            ip_db = IPAddr(node=node_id, ip_addr=ip, admin=True)
            orm().add(ip_db)
        orm().commit()


def assign_ips(nodes_ids, network_name):
    """Idempotent assignment IP addresses to nodes.

    All nodes passed as first argument get IP address from
    network, referred by network_name.
    If node already has IP address from this network, it remains unchanged.
    If one of the nodes is the node from other cluster, this func will fail.

    """
    cluster_id = orm().query(Node).get(nodes_ids[0]).cluster_id
    for node_id in nodes_ids:
        node = orm().query(Node).get(node_id)
        if node.cluster_id != cluster_id:
            raise Exception("Node id='%s' doesn't belong to cluster_id='%s'" %
                            (node_id, cluster_id))

    network = orm().query(Network).join(NetworkGroup).\
        filter(NetworkGroup.cluster_id == cluster_id).\
        filter_by(name=network_name).first()

    if not network:
        raise errors.AssignIPError(
            "Network '%s' for cluster_id=%s not found." %
            (network_name, cluster_id)
        )

    for node_id in nodes_ids:
        node_ips = [ne.ip_addr for ne in orm().query(IPAddr).
                    filter_by(node=node_id).
                    filter_by(admin=False).
                    filter_by(network=network.id).all() if ne.ip_addr]
        # check if any of node_ips in required cidr: network.cidr
        ips_belongs_to_net = IPSet(IPNetwork(network.cidr))\
            .intersection(IPSet(node_ips))

        if not ips_belongs_to_net:
            # IP address has not been assigned, let's do it
            from_range = set(
                [str(i) for i in IPNetwork(network.cidr).iter_hosts()]
            ) - set((network.gateway,))
            free_ips = get_free_ip_from_range(from_range)
            ip_db = IPAddr(
                network=network.id,
                node=node_id,
                ip_addr=free_ips[0]
            )
            orm().add(ip_db)
            orm().commit()


def assign_vip(cluster_id, network_name):
    """Idempotent assignment VirtualIP addresses to cluster.
    Returns VIP for given cluster and network.

    It's required for HA deployment to have IP address not assigned to any
      of nodes. Currently we need one VIP per network in cluster.
    If cluster already has IP address from this network, it remains unchanged.
    If one of the nodes is the node from other cluster, this func will fail.

    """
    cluster = orm().query(Cluster).get(cluster_id)
    if not cluster:
        raise Exception("Cluster id='%s' not found" % cluster_id)

    network = orm().query(Network).join(NetworkGroup).\
        filter(NetworkGroup.cluster_id == cluster_id).\
        filter_by(name=network_name).first()

    if not network:
        raise Exception("Network '%s' for cluster_id=%s not found." %
                        (network_name, cluster_id))

    cluster_ips = [ne.ip_addr for ne in orm().query(IPAddr).filter_by(
        network=network.id,
        node=None,
        admin=False
    ).all()]
    # check if any of used_ips in required cidr: network.cidr
    ips_belongs_to_net = IPSet(IPNetwork(network.cidr))\
        .intersection(IPSet(cluster_ips))

    if ips_belongs_to_net:
        vip = cluster_ips[0]
    else:
        # IP address has not been assigned, let's do it
        from_range = set(
            [str(i) for i in IPNetwork(network.cidr).iter_hosts()]
        ) - set((network.gateway,))
        free_ips = get_free_ip_from_range(from_range)
        ne_db = IPAddr(network=network.id, ip_addr=free_ips[0])
        orm().add(ne_db)
        orm().commit()
        vip = free_ips[0]
    return vip


def get_node_networks(node_id):
    cluster_db = orm().query(Node).get(node_id).cluster
    if cluster_db is None:
        # Node doesn't belong to any cluster, so it should not have nets
        return []
    ips = orm().query(IPAddr).\
        filter_by(node=node_id).\
        filter_by(admin=False).all()
    network_data = []
    network_ids = []
    for i in ips:
        net = orm().query(Network).get(i.network)
        network_data.append({
            'name': net.name,
            'vlan': net.vlan_id,
            'ip': i.ip_addr + '/' + str(IPNetwork(net.cidr).prefixlen),
            'netmask': str(IPNetwork(net.cidr).netmask),
            'brd': str(IPNetwork(net.cidr).broadcast),
            'gateway': net.gateway,
            'dev': 'eth0'})  # We need to figure out interface
        network_ids.append(net.id)
    # And now let's add networks w/o IP addresses
    nets = orm().query(Network).join(NetworkGroup).\
        filter(NetworkGroup.cluster_id == cluster_db.id)
    if network_ids:
        nets = nets.filter(not_(Network.id.in_(network_ids)))
    # For now, we pass information about all networks,
    #    so these vlans will be created on every node we call this func for
    # However it will end up with errors if we precreate vlans in VLAN mode
    #   in fixed network. We are skipping fixed nets in Vlan mode.
    for net in nets.all():
        if net.name == 'fixed' and cluster_db.net_manager == 'VlanManager':
            continue
        network_data.append({
            'name': net.name,
            'vlan': net.vlan_id,
            'dev': 'eth0'})

    return network_data
