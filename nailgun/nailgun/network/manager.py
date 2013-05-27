# -*- coding: utf-8 -*-

import math
from itertools import imap, ifilter, islice, chain, tee

import web
from sqlalchemy.sql import not_
from netaddr import IPSet, IPNetwork, IPRange

from nailgun.db import orm
from nailgun.errors import errors
from nailgun.logger import logger
from nailgun.settings import settings
from nailgun.api.models import Node, NodeNICInterface, IPAddr, Cluster, Vlan
from nailgun.api.models import Network, NetworkGroup, IPAddrRange


class NetworkManager(object):

    def __init__(self, db=None):
        self.db = db or orm()

    def get_admin_network_id(self, fail_if_not_found=True):
        admin_net = self.db.query(Network).filter_by(
            name="fuelweb_admin"
        ).first()
        if not admin_net and fail_if_not_found:
            raise errors.AdminNetworkNotFound()
        return admin_net.id

    def create_network_groups(self, cluster_id):
        used_nets = [n.cidr for n in self.db.query(Network).all()]
        used_vlans = [v.id for v in self.db.query(Vlan).all()]

        cluster_db = self.db.query(Cluster).get(cluster_id)

        for network in cluster_db.release.networks_metadata:
            free_vlans = sorted(list(set(range(int(
                settings.VLANS_RANGE_START),
                int(settings.VLANS_RANGE_END))) -
                set(used_vlans)))
            if not free_vlans:
                raise errors.OutOfVLANs()
            vlan_start = free_vlans[0]
            logger.debug("Found free vlan: %s", vlan_start)

            pool = settings.NETWORK_POOLS[network['access']]
            nets_free_set = IPSet(pool) -\
                IPSet(settings.NET_EXCLUDE) -\
                IPSet(
                    IPRange(
                        settings.ADMIN_NETWORK["first"],
                        settings.ADMIN_NETWORK["last"]
                    )
                ) -\
                IPSet(used_nets)
            if not nets_free_set:
                raise errors.OutOfIPs()

            free_cidrs = sorted(list(nets_free_set._cidrs))
            new_net = None
            for fcidr in free_cidrs:
                for n in fcidr.subnet(24, count=1):
                    new_net = n
                    break
                if new_net:
                    break
            if not new_net:
                raise errors.NoSuitableCIDR()

            new_ip_range = IPAddrRange(
                first=str(new_net[2]),
                last=str(new_net[-2]),
                netmask=str(new_net.netmask)
            )

            nw_group = NetworkGroup(
                release=cluster_db.release.id,
                name=network['name'],
                access=network['access'],
                cidr=str(new_net),
                gateway_ip_index=1,
                cluster_id=cluster_id,
                vlan_start=vlan_start,
                amount=1
            )
            self.db.add(nw_group)
            self.db.commit()
            nw_group.ip_ranges.append(new_ip_range)
            self.db.commit()
            self.create_networks(nw_group)

            used_vlans.append(vlan_start)
            used_nets.append(str(new_net))

    def create_networks(self, nw_group):
        fixnet = IPNetwork(nw_group.cidr)
        subnet_bits = int(math.ceil(math.log(nw_group.network_size, 2)))
        logger.debug("Specified network size requires %s bits", subnet_bits)
        subnets = list(fixnet.subnet(32 - subnet_bits,
                                     count=nw_group.amount))
        logger.debug("Base CIDR sliced on subnets: %s", subnets)

        for net in nw_group.networks:
            logger.debug("Deleting old network with id=%s, cidr=%s",
                         net.id, net.cidr)
            ips = self.db.query(IPAddr).filter(
                IPAddr.network == net.id
            ).all()
            map(self.db.delete, ips)
            self.db.delete(net)
            self.db.commit()
        # Dmitry's hack for clearing VLANs without networks
        self.clear_vlans()
        self.db.commit()
        nw_group.networks = []

        for n in xrange(nw_group.amount):
            vlan_db = self.db.query(Vlan).get(nw_group.vlan_start + n)
            if vlan_db:
                logger.warning("Intersection with existing vlan_id: %s",
                               vlan_db.id)
            else:
                vlan_db = Vlan(id=nw_group.vlan_start + n)
                self.db.add(vlan_db)
            logger.debug("Created VLAN object, vlan_id=%s", vlan_db.id)
            gateway = None
            if nw_group.gateway_ip_index:
                gateway = str(subnets[n][nw_group.gateway_ip_index])
            net_db = Network(
                release=nw_group.release,
                name=nw_group.name,
                access=nw_group.access,
                cidr=str(subnets[n]),
                vlan_id=vlan_db.id,
                gateway=gateway,
                network_group_id=nw_group.id)
            self.db.add(net_db)
        self.db.commit()

    def assign_admin_ips(self, node_id, num=1):
        admin_net_id = self.get_admin_network_id()
        node_admin_ips = self.db.query(IPAddr).filter_by(
            node=node_id,
            network=admin_net_id
        ).all()

        if not node_admin_ips or len(node_admin_ips) < num:
            logger.debug(
                "Trying to assign admin ips: node=%s count=%s",
                node_id,
                num - len(node_admin_ips)
            )
            free_ips = self._get_free_ips_from_range(
                imap(str, IPRange(
                    settings.ADMIN_NETWORK['first'],
                    settings.ADMIN_NETWORK['last']
                )),
                num=num - len(node_admin_ips)
            )
            for ip in free_ips:
                ip_db = IPAddr(
                    node=node_id,
                    ip_addr=ip,
                    network=admin_net_id
                )
                self.db.add(ip_db)
            self.db.commit()

    def assign_ips(self, nodes_ids, network_name):
        """
        Idempotent assignment IP addresses to nodes.

        All nodes passed as first argument get IP address
        from network, referred by network_name.
        If node already has IP address from this network,
        it remains unchanged. If one of the nodes is the
        node from other cluster, this func will fail.
        """

        cluster_id = self.db.query(Node).get(nodes_ids[0]).cluster_id
        for node_id in nodes_ids:
            node = self.db.query(Node).get(node_id)
            if node.cluster_id != cluster_id:
                raise Exception(
                    u"Node id='{0}' doesn't belong to cluster_id='{1}'".format(
                        node_id,
                        cluster_id
                    )
                )

        network = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_id).\
            filter_by(name=network_name).first()

        if not network:
            raise errors.AssignIPError(
                "Network '%s' for cluster_id=%s not found." %
                (network_name, cluster_id)
            )

        for node_id in nodes_ids:
            node_ips = map(
                lambda i: i.ip_addr,
                self._get_ips_except_admin(
                    node_id=node_id,
                    network_id=network.id
                )
            )
            # check if any of node_ips in required cidr: network.cidr
            ips_belongs_to_net = IPSet(IPNetwork(network.cidr))\
                .intersection(IPSet(node_ips))

            if not ips_belongs_to_net:
                # IP address has not been assigned, let's do it
                from_range = ifilter(
                    lambda x: x not in (network.gateway,),
                    imap(
                        str,
                        IPNetwork(network.cidr).iter_hosts()
                    )
                )
                free_ips = self._get_free_ips_from_range(from_range)
                ip_db = IPAddr(
                    network=network.id,
                    node=node_id,
                    ip_addr=free_ips[0]
                )
                self.db.add(ip_db)
                self.db.commit()

    def assign_vip(self, cluster_id, network_name):
        """
        Idempotent assignment VirtualIP addresses to cluster.
        Returns VIP for given cluster and network.

        It's required for HA deployment to have IP address
        not assigned to any of nodes. Currently we need one
        VIP per network in cluster. If cluster already has
        IP address from this network, it remains unchanged.
        If one of the nodes is the node from other cluster,
        this func will fail.
        """

        cluster = self.db.query(Cluster).get(cluster_id)
        if not cluster:
            raise Exception("Cluster id='%s' not found" % cluster_id)

        network = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_id).\
            filter_by(name=network_name).first()

        if not network:
            raise Exception("Network '%s' for cluster_id=%s not found." %
                            (network_name, cluster_id))

        admin_net_id = self.get_admin_network_id()
        cluster_ips = [ne.ip_addr for ne in self.db.query(IPAddr).filter_by(
            network=network.id,
            node=None
        ).filter(
            not_(IPAddr.network == admin_net_id)
        ).all()]
        # check if any of used_ips in required cidr: network.cidr
        ips_belongs_to_net = IPSet(IPNetwork(network.cidr))\
            .intersection(IPSet(cluster_ips))

        if ips_belongs_to_net:
            vip = cluster_ips[0]
        else:
            # IP address has not been assigned, let's do it
            from_range = ifilter(
                lambda x: x not in (network.gateway,),
                imap(
                    str,
                    IPNetwork(network.cidr).iter_hosts()
                )
            )
            free_ips = self._get_free_ips_from_range(from_range)
            vip = free_ips[0]
            ne_db = IPAddr(network=network.id, ip_addr=vip)
            self.db.add(ne_db)
            self.db.commit()
        return vip

    def clear_vlans(self):
        map(
            self.db.delete,
            self.db.query(Vlan).filter_by(network=None)
        )
        self.db.commit()

    @classmethod
    def _chunked_range(cls, iterable, chunksize=64):
        """
        We want to be able to iterate over iterable chunk by chunk.
        We instantiate iter object from itarable. We then yield
        iter instance slice in infinite loop. Iter slice starts
        from the last used position and finishes on the position
        which is offset with chunksize from the last used position.
        """
        it = iter(iterable)
        while True:
            s = islice(it, chunksize)
            # Here we check if iterator is not empty calling
            # next() method which raises StopInteration if
            # iter is empty. If iter is not empty we yield
            # iterator which is concatenation of fisrt element in
            # slice and the ramained elements.
            yield chain([s.next()], s)

    def _get_free_ips_from_range(self, iterable, num=1):
        free_ips = []
        for chunk in self._chunked_range(iterable):
            from_range = set(chunk)
            diff = from_range - set(
                [i.ip_addr for i in self.db.query(IPAddr).
                 filter(IPAddr.ip_addr.in_(from_range))]
            )
            while len(free_ips) < num:
                try:
                    free_ips.append(diff.pop())
                except KeyError:
                    break
            if len(free_ips) == num:
                return free_ips
        raise errors.OutOfIPs()

    def _get_ips_except_admin(self, node_id=None, network_id=None):
        node_db = self.db.query(Node).get(node_id)
        ips = self.db.query(IPAddr).order_by(IPAddr.id)
        if node_id:
            ips = ips.filter_by(node=node_id)
        if network_id:
            ips = ips.filter_by(network=network_id)

        admin_net_id = self.get_admin_network_id(False)
        if admin_net_id:
            ips = ips.filter(
                not_(IPAddr.network == admin_net_id)
            )

        return ips.all()

    def get_node_networks(self, node_id):
        """
        Get dictionary with all networks of specified node
        """
        node_db = self.db.query(Node).get(node_id)
        cluster_db = node_db.cluster
        if cluster_db is None:
            # Node doesn't belong to any cluster, so it should not have nets
            return []

        ips = self._get_ips_except_admin(node_id=node_id)
        network_data = []
        network_ids = []
        for i in ips:
            net = self.db.query(Network).get(i.network)
            interface = self._get_interface_by_network_name(node_db, net.name)

            network_data.append({
                'name': net.name,
                'vlan': net.vlan_id,
                'ip': i.ip_addr + '/' + str(IPNetwork(net.cidr).prefixlen),
                'netmask': str(IPNetwork(net.cidr).netmask),
                'brd': str(IPNetwork(net.cidr).broadcast),
                'gateway': net.gateway,
                'dev': interface.name})
            network_ids.append(net.id)

        # And now let's add networks w/o IP addresses
        nets = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_db.id)
        if network_ids:
            nets = nets.filter(not_(Network.id.in_(network_ids)))

        # For now, we pass information about all networks,
        #    so these vlans will be created on every node we call this func for
        # However it will end up with errors if we precreate vlans in VLAN mode
        #   in fixed network. We are skipping fixed nets in Vlan mode.
        for net in nets.order_by(Network.id).all():
            interface = self._get_interface_by_network_name(node_db, net.name)

            if net.name == 'fixed' and cluster_db.net_manager == 'VlanManager':
                continue
            network_data.append({
                'name': net.name,
                'vlan': net.vlan_id,
                'dev': interface.name})

        return network_data

    def update_interfaces_info(self, node):
        if not "interfaces" in node.meta:
            raise Exception("No interfaces metadata specified for node")

        for interface in node.meta["interfaces"]:
            nicInterface = NodeNICInterface()
            nicInterface.node_id = node.id
            nicInterface.name = interface["name"]
            nicInterface.mac = interface["mac"]
            if "max_speed" in interface:
                nicInterface.max_speed = interface["max_speed"]
            if "current_speed" in interface:
                nicInterface.current_speed = interface["current_speed"]
            self.db.add(nicInterface)
            self.db.commit()
            node.interfaces.append(nicInterface)

    def _get_interface_by_network_name(self, node, network_name):
        """
        Return network device which has appointed
        network with specified network name
        """
        for interface in node.interfaces:
            for network in interface.assigned_networks:
                if network.name == network_name:
                    return interface
