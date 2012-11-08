# -*- coding: utf-8 -*-

import web
from netaddr import IPSet, IPNetwork

from nailgun.api.models import Network, Node, IPAddr


def assign_ips(cluster_id, network_name):
    """Idempotent assignment IP addresses to nodes.

    All nodes in cluster referred by cluster_id get IP address from
    network, referred by network_name.
    If node already has IP address from this network, it remains unchanged.

    """
    nodes = web.ctx.orm.query(Node).filter_by(cluster_id=cluster_id).all()
    network = web.ctx.orm.query(Network).\
        filter_by(cluster_id=cluster_id).\
        filter_by(name=network_name).first()

    if not network:
        raise Exception("Network '%s' for cluster_id=%s not found." %
                        (network_name, cluster_id))

    used_ips = [n.ip_addr for n in web.ctx.orm.query(IPAddr).all()]

    for node in nodes:
        node_ips = [n.ip_addr for n in web.ctx.orm.query(IPAddr).
                    filter_by(node=node.id).
                    filter_by(network=network.id).all()]

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
            ip_db = IPAddr(network=network.id, node=node.id, ip_addr=free_ip)
            web.ctx.orm.add(ip_db)
            web.ctx.orm.commit()
            used_ips.append(free_ip)


def get_node_networks(node_id):
    ips = web.ctx.orm.query(IPAddr).filter_by(node=node_id).all()
    network_data = []
    for i in ips:
        net = web.ctx.orm.query(Network).get(i.network)
        network_data.append({
            'vlan': net.vlan_id,
            'ip': i.ip_addr + '/' + str(IPNetwork(net.cidr).prefixlen),
            'brd': str(IPNetwork(net.cidr).broadcast),
            'gateway': net.gateway,
            'dev': 'eth0'})  # We need to figure out interface
    return network_data
