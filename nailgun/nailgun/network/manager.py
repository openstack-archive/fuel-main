# -*- coding: utf-8 -*-

import web
from sqlalchemy.sql import not_
from netaddr import IPSet, IPNetwork

from nailgun.db import orm
from nailgun.task import errors
from nailgun.api.models import Node, NetworkElement, Cluster
from nailgun.api.models import Network, NetworkGroup


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

    used_ips = [ne.ip_addr for ne in orm().query(NetworkElement).all()
                if ne.ip_addr]

    for node_id in nodes_ids:
        node_ips = [ne.ip_addr for ne in orm().query(NetworkElement).
                    filter_by(node=node_id).
                    filter_by(network=network.id).all() if ne.ip_addr]
        # check if any of node_ips in required cidr: network.cidr
        ips_belongs_to_net = IPSet(IPNetwork(network.cidr))\
            .intersection(IPSet(node_ips))

        if not ips_belongs_to_net:
            # IP address has not been assigned, let's do it
            free_ip = None
            for ip in IPNetwork(network.cidr).iter_hosts():
                # iter_hosts iterates over network, excludes net & broadcast
                if str(ip) != network.gateway and str(ip) not in used_ips:
                    free_ip = str(ip)
                    break
            if not free_ip:
                raise Exception(
                    "Network pool %s ran out of free ips." % network.cidr)

            ip_db = NetworkElement(network=network.id, node=node_id,
                                   ip_addr=free_ip)
            orm().add(ip_db)
            orm().commit()
            used_ips.append(free_ip)


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

    used_ips = [ne.ip_addr for ne in orm().query(NetworkElement).all()
                if ne.ip_addr]

    cluster_ips = [ne.ip_addr for ne in orm().query(NetworkElement).
                   filter_by(network=network.id).
                   filter_by(node=None).all() if ne.ip_addr]
    # check if any of used_ips in required cidr: network.cidr
    ips_belongs_to_net = IPSet(IPNetwork(network.cidr))\
        .intersection(IPSet(cluster_ips))

    if ips_belongs_to_net:
        vip = cluster_ips[0]
    else:
        # IP address has not been assigned, let's do it
        free_ip = None
        for ip in IPNetwork(network.cidr).iter_hosts():
            # iter_hosts iterates over network, excludes net & broadcast
            if str(ip) != network.gateway and str(ip) not in used_ips:
                free_ip = str(ip)
                break

        if not free_ip:
            raise Exception(
                "Network pool %s ran out of free ips." % network.cidr)
        ne_db = NetworkElement(network=network.id, ip_addr=free_ip)
        orm().add(ne_db)
        orm().commit()
        vip = free_ip
    return vip


def get_node_networks(node_id):
    cluster_id = orm().query(Node).get(node_id).cluster_id
    ips = [x for x in orm().query(NetworkElement).filter_by(
        node=node_id).all() if x.ip_addr]  # Got rid of Nones (if x.ip_addr)
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
        filter(NetworkGroup.cluster_id == cluster_id)
    if network_ids:
        nets = nets.filter(not_(Network.id.in_(network_ids)))
    # For now, we pass information about all networks,
    #    so these vlans will be created on every node we call this func for
    for net in nets.all():
        network_data.append({
            'name': net.name,
            'vlan': net.vlan_id,
            'dev': 'eth0'})

    return network_data
