# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import math
from itertools import imap, ifilter, islice, chain, tee

import web
from sqlalchemy.sql import not_
from netaddr import IPSet, IPNetwork, IPRange, IPAddress

from nailgun.db import db
from nailgun.errors import errors
from nailgun.logger import logger
from nailgun.settings import settings
from nailgun.api.models import NetworkAssignment
from nailgun.api.models import Node, NodeNICInterface, IPAddr, Cluster, Vlan
from nailgun.api.models import Network, NetworkGroup, IPAddrRange


class NetworkManager(object):

    def update_ranges_from_cidr(self, network_group, cidr):
        """
        Update network ranges for cidr
        """
        db().query(IPAddrRange).filter_by(
            network_group_id=network_group.id).delete()

        new_cidr = IPNetwork(cidr)
        ip_range = IPAddrRange(
            network_group_id=network_group.id,
            first=str(new_cidr[2]),
            last=str(new_cidr[-2]))

        db().add(ip_range)
        db().commit()

    def get_admin_network_id(self, fail_if_not_found=True):
        '''
        Method for receiving Admin Network ID.

        :param fail_if_not_found: Raise an error
        if admin network is not found in database.
        :type  fail_if_not_found: bool
        :returns: Admin Network ID or None.
        :raises: errors.AdminNetworkNotFound
        '''
        admin_net = db().query(Network).filter_by(
            name="fuelweb_admin"
        ).first()
        if not admin_net and fail_if_not_found:
            raise errors.AdminNetworkNotFound()
        return admin_net.id

    def create_network_groups(self, cluster_id):
        '''
        Method for creation of network groups for cluster.

        :param cluster_id: Cluster database ID.
        :type  cluster_id: int
        :returns: None
        :raises: errors.OutOfVLANs, errors.OutOfIPs,
        errors.NoSuitableCIDR
        '''
        used_nets = [n.cidr for n in db().query(Network).all()]
        used_vlans = [v.id for v in db().query(Vlan).all()]

        cluster_db = db().query(Cluster).get(cluster_id)

        networks_metadata = cluster_db.release.networks_metadata

        def _free_vlans():
            free_vlans = set(
                range(
                    int(settings.VLANS_RANGE_START),
                    int(settings.VLANS_RANGE_END)
                )
            ) - set(used_vlans)
            if not free_vlans or len(free_vlans) < len(networks_metadata):
                raise errors.OutOfVLANs()
            return sorted(list(free_vlans))

        public_vlan = _free_vlans()[0]
        used_vlans.append(public_vlan)
        for network in networks_metadata:
            free_vlans = _free_vlans()
            vlan_start = public_vlan if network['access'] == 'public' \
                else free_vlans[0]

            logger.debug("Found free vlan: %s", vlan_start)
            pool = settings.NETWORK_POOLS[network['access']]
            if not pool:
                raise errors.InvalidNetworkAccess(
                    u"Invalid access '{0}' for network '{1}'".format(
                        network['access'],
                        network['name']
                    )
                )
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
                last=str(new_net[-2])
            )

            nw_group = NetworkGroup(
                release=cluster_db.release.id,
                name=network['name'],
                access=network['access'],
                cidr=str(new_net),
                netmask=str(new_net.netmask),
                gateway=str(new_net[1]),
                cluster_id=cluster_id,
                vlan_start=vlan_start,
                amount=1
            )
            db().add(nw_group)
            db().commit()
            nw_group.ip_ranges.append(new_ip_range)
            db().commit()
            self.create_networks(nw_group)

            used_vlans.append(vlan_start)
            used_nets.append(str(new_net))

    def create_networks(self, nw_group):
        '''
        Method for creation of networks for network group.

        :param nw_group: NetworkGroup object.
        :type  nw_group: NetworkGroup
        :returns: None
        '''
        fixnet = IPNetwork(nw_group.cidr)
        subnet_bits = int(math.ceil(math.log(nw_group.network_size, 2)))
        logger.debug("Specified network size requires %s bits", subnet_bits)
        subnets = list(fixnet.subnet(32 - subnet_bits,
                                     count=nw_group.amount))
        logger.debug("Base CIDR sliced on subnets: %s", subnets)

        for net in nw_group.networks:
            logger.debug("Deleting old network with id=%s, cidr=%s",
                         net.id, net.cidr)
            ips = db().query(IPAddr).filter(
                IPAddr.network == net.id
            ).all()
            map(db().delete, ips)
            db().delete(net)
            db().commit()
        # Dmitry's hack for clearing VLANs without networks
        self.clear_vlans()
        db().commit()
        nw_group.networks = []

        for n in xrange(nw_group.amount):
            vlan_id = None
            if nw_group.vlan_start is not None:
                vlan_db = db().query(Vlan).get(nw_group.vlan_start + n)
                if vlan_db:
                    logger.warning("Intersection with existing vlan_id: %s",
                                   vlan_db.id)
                else:
                    vlan_db = Vlan(id=nw_group.vlan_start + n)
                    db().add(vlan_db)
                vlan_id = vlan_db.id
                logger.debug("Created VLAN object, vlan_id=%s", vlan_id)
            gateway = None
            if nw_group.gateway:
                gateway = nw_group.gateway
            net_db = Network(
                release=nw_group.release,
                name=nw_group.name,
                access=nw_group.access,
                cidr=str(subnets[n]),
                vlan_id=vlan_id,
                gateway=gateway,
                network_group_id=nw_group.id)
            db().add(net_db)
        db().commit()

    def assign_admin_ips(self, node_id, num=1):
        '''
        Method for assigning admin IP addresses to nodes.

        :param node_id: Node database ID.
        :type  node_id: int
        :param num: Number of IP addresses for node.
        :type  num: int
        :returns: None
        '''
        admin_net_id = self.get_admin_network_id()
        node_admin_ips = db().query(IPAddr).filter_by(
            node=node_id,
            network=admin_net_id
        ).all()

        if not node_admin_ips or len(node_admin_ips) < num:
            admin_net = db().query(Network).get(admin_net_id)
            logger.debug(
                u"Trying to assign admin ips: node=%s count=%s",
                node_id,
                num - len(node_admin_ips)
            )
            free_ips = self.get_free_ips(
                admin_net.network_group.id,
                num=num - len(node_admin_ips)
            )
            logger.info(len(free_ips))
            for ip in free_ips:
                ip_db = IPAddr(
                    node=node_id,
                    ip_addr=ip,
                    network=admin_net_id
                )
                db().add(ip_db)
            db().commit()

    def assign_ips(self, nodes_ids, network_name):
        """
        Idempotent assignment IP addresses to nodes.

        All nodes passed as first argument get IP address
        from network, referred by network_name.
        If node already has IP address from this network,
        it remains unchanged. If one of the nodes is the
        node from other cluster, this func will fail.

        :param node_ids: List of nodes IDs in database.
        :type  node_ids: list
        :param network_name: Network name
        :type  network_name: str
        :returns: None
        :raises: Exception, errors.AssignIPError
        """

        cluster_id = db().query(Node).get(nodes_ids[0]).cluster_id
        for node_id in nodes_ids:
            node = db().query(Node).get(node_id)
            if node.cluster_id != cluster_id:
                raise Exception(
                    u"Node id='{0}' doesn't belong to cluster_id='{1}'".format(
                        node_id,
                        cluster_id
                    )
                )

        network = db().query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_id).\
            filter_by(name=network_name).first()

        if not network:
            raise errors.AssignIPError(
                u"Network '%s' for cluster_id=%s not found." %
                (network_name, cluster_id)
            )

        for node_id in nodes_ids:
            node_ips = imap(
                lambda i: i.ip_addr,
                self._get_ips_except_admin(
                    node_id=node_id,
                    network_id=network.id
                )
            )
            # check if any of node_ips in required ranges
            for ip in node_ips:
                if self.check_ip_belongs_to_net(ip, network):
                    logger.info(
                        u"Node id='{0}' already has an IP address "
                        "inside '{1}' network.".format(
                            node.id,
                            network.name
                        )
                    )
                    continue

            # IP address has not been assigned, let's do it
            free_ip = self.get_free_ips(network.network_group.id)[0]
            ip_db = IPAddr(
                network=network.id,
                node=node_id,
                ip_addr=free_ip
            )
            db().add(ip_db)
            db().commit()

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

        :param cluster_id: Cluster database ID.
        :type  cluster_id: int
        :param network_name: Network name
        :type  network_name: str
        :returns: None
        :raises: Exception
        """

        cluster = db().query(Cluster).get(cluster_id)
        if not cluster:
            raise Exception(u"Cluster id='%s' not found" % cluster_id)

        network = db().query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_id).\
            filter_by(name=network_name).first()

        if not network:
            raise Exception(u"Network '%s' for cluster_id=%s not found." %
                            (network_name, cluster_id))

        admin_net_id = self.get_admin_network_id()
        cluster_ips = [ne.ip_addr for ne in db().query(IPAddr).filter_by(
            network=network.id,
            node=None
        ).filter(
            not_(IPAddr.network == admin_net_id)
        ).all()]
        # check if any of used_ips in required cidr: network.cidr
        ips_belongs_to_net = False
        for ip in cluster_ips:
            if self.check_ip_belongs_to_net(ip, network):
                ips_belongs_to_net = True
                break

        if ips_belongs_to_net:
            vip = cluster_ips[0]
        else:
            # IP address has not been assigned, let's do it
            vip = self.get_free_ips(network.network_group.id)[0]
            ne_db = IPAddr(network=network.id, ip_addr=vip)
            db().add(ne_db)
            db().commit()
        return vip

    def clear_vlans(self):
        """
        Removes from DB all Vlans without Networks assigned to them.
        """
        map(
            db().delete,
            db().query(Vlan).filter_by(network=None)
        )
        db().commit()

    @classmethod
    def _chunked_range(cls, iterable, chunksize=64):
        """
        We want to be able to iterate over iterable chunk by chunk.
        We instantiate iter object from itarable. We then yield
        iter instance slice in infinite loop. Iter slice starts
        from the last used position and finishes on the position
        which is offset with chunksize from the last used position.

        :param iterable: Iterable object.
        :type  iterable: iterable
        :param chunksize: Size of chunk to iterate through.
        :type  chunksize: int
        :yields: iterator
        :raises: StopIteration
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

    def check_ip_belongs_to_net(self, ip_addr, network):
        addr = IPAddress(ip_addr)
        ipranges = imap(
            lambda ir: IPRange(ir.first, ir.last),
            network.network_group.ip_ranges
        )
        for r in ipranges:
            if addr in r:
                return True
        return False

    def _iter_free_ips(self, network_group):
        """
        Represents iterator over free IP addresses
        in all ranges for given Network Group
        """
        for ip_addr in ifilter(
            lambda ip: db().query(IPAddr).filter_by(
                ip_addr=str(ip)
            ).first() is None and not ip == network_group.gateway,
            chain(*[
                IPRange(ir.first, ir.last)
                for ir in network_group.ip_ranges
            ])
        ):
            yield ip_addr

    def get_free_ips(self, network_group_id, num=1):
        """
        Returns list of free IP addresses for given Network Group
        """
        ng = db().query(NetworkGroup).get(network_group_id)
        free_ips = []
        for ip in self._iter_free_ips(ng):
            free_ips.append(str(ip))
            if len(free_ips) == num:
                break
        if len(free_ips) < num:
            raise errors.OutOfIPs()
        return free_ips

    def _get_free_ips_from_range(self, iterable, num=1):
        """
        Method for receiving free IP addresses from range.

        :param iterable: Iterable object with IP addresses.
        :type  iterable: iterable
        :param num: Number of IP addresses to return.
        :type  num: int
        :returns: List of free IP addresses from given range.
        :raises: errors.OutOfIPs
        """
        free_ips = []
        for chunk in self._chunked_range(iterable):
            from_range = set(chunk)
            diff = from_range - set(
                [i.ip_addr for i in db().query(IPAddr).
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
        """
        Method for receiving IP addresses for node or network
        excluding Admin Network IP address.

        :param node_id: Node database ID.
        :type  node_id: int
        :param network_id: Network database ID.
        :type  network_id: int
        :returns: List of free IP addresses as SQLAlchemy objects.
        """
        node_db = db().query(Node).get(node_id)
        ips = db().query(IPAddr).order_by(IPAddr.id)
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

    def get_main_nic(self, node_id):
        node_db = db().query(Node).get(node_id)
        for nic in node_db.interfaces:
            if node_db.mac == nic.mac:
                return nic.id
        # we need at least one interface here - so let's
        # take the first one
        if node_db.interfaces:
            return node_db.interfaces[0].id

    def clear_all_allowed_networks(self, node_id):
        node_db = db().query(Node).get(node_id)
        for nic in node_db.interfaces:
            while nic.allowed_networks:
                nic.allowed_networks.pop()
        db().commit()

    def clear_assigned_networks(self, node_id):
        node_db = db().query(Node).get(node_id)
        for nic in node_db.interfaces:
            while nic.assigned_networks:
                nic.assigned_networks.pop()
        db().commit()

    def get_cluster_networkgroups_by_node(self, node_id):
        """
        Method for receiving cluster network groups by node.

        :param node: Node object.
        :type  node: Node
        :returns: List of network groups for cluster node belongs to.
        """
        node_db = db().query(Node).get(node_id)
        if node_db.cluster:
            return [ng.id for ng in node_db.cluster.network_groups]
        return []

    def allow_network_assignment_to_all_interfaces(self, node_id):
        """
        Method adds all network groups from cluster
        to allowed_networks list for all interfaces
        of specified node.

        :param node: Node object.
        :type  node: Node
        """
        node_db = db().query(Node).get(node_id)
        for nic in node_db.interfaces:
            for net_group_id in self.get_cluster_networkgroups_by_node(
                node_id
            ):
                ng_db = db().query(NetworkGroup).get(net_group_id)
                nic.allowed_networks.append(ng_db)
        db().commit()

    def assign_networks_to_main_interface(self, node_id):
        self.clear_assigned_networks(node_id)
        main_nic_id = self.get_main_nic(node_id)
        if main_nic_id:
            main_nic = db().query(NodeNICInterface).get(main_nic_id)
            for net_group_id in self.get_cluster_networkgroups_by_node(
                node_id
            ):
                ng_db = db().query(NetworkGroup).get(net_group_id)
                main_nic.assigned_networks.append(ng_db)
            db().commit()

    def get_node_networks(self, node_id):
        """
        Method for receiving network data for a given node.

        :param node_id: Node database ID.
        :type  node_id: int
        :returns: List of network info for node.
        """
        node_db = db().query(Node).get(node_id)
        cluster_db = node_db.cluster
        if cluster_db is None:
            # Node doesn't belong to any cluster, so it should not have nets
            return []

        ips = self._get_ips_except_admin(node_id=node_id)
        network_data = []
        network_ids = []
        for i in ips:
            net = db().query(Network).get(i.network)
            interface = self._get_interface_by_network_name(
                node_db.id,
                net.name
            )

            # Get prefix from netmask instead of cidr
            # for public network
            if net.name == 'public':
                network_group = db().query(NetworkGroup).get(
                    net.network_group_id)

                # Convert netmask to prefix
                prefix = str(IPNetwork(
                    '0.0.0.0/' + network_group.netmask).prefixlen)
                netmask = network_group.netmask
            else:
                prefix = str(IPNetwork(net.cidr).prefixlen)
                netmask = str(IPNetwork(net.cidr).netmask)

            network_data.append({
                'name': net.name,
                'vlan': net.vlan_id,
                'ip': i.ip_addr + '/' + prefix,
                'netmask': netmask,
                'brd': str(IPNetwork(net.cidr).broadcast),
                'gateway': net.gateway,
                'dev': interface.name})
            network_ids.append(net.id)

        # And now let's add networks w/o IP addresses
        nets = db().query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_db.id)
        if network_ids:
            nets = nets.filter(not_(Network.id.in_(network_ids)))

        # For now, we pass information about all networks,
        #    so these vlans will be created on every node we call this func for
        # However it will end up with errors if we precreate vlans in VLAN mode
        #   in fixed network. We are skipping fixed nets in Vlan mode.
        for net in nets.order_by(Network.id).all():
            interface = self._get_interface_by_network_name(
                node_db.id,
                net.name
            )

            if net.name == 'fixed' and cluster_db.net_manager == 'VlanManager':
                continue
            network_data.append({
                'name': net.name,
                'vlan': net.vlan_id,
                'dev': interface.name})

        network_data.append(self._get_admin_network(node_db))

        return network_data

    def _update_attrs(self, node_data):
        node_db = db().query(Node).get(node_data['id'])
        interfaces = node_data['interfaces']
        interfaces_db = node_db.interfaces
        for iface in interfaces:
            current_iface = filter(
                lambda i: i.id == iface['id'],
                interfaces_db
            )[0]
            # Remove all old network's assignment for this interface.
            db().query(NetworkAssignment).filter_by(
                interface_id=current_iface.id
            ).delete()
            for net in iface['assigned_networks']:
                net_assignment = NetworkAssignment()
                net_assignment.network_id = net['id']
                net_assignment.interface_id = current_iface.id
                db().add(net_assignment)
        db().commit()
        return node_db.id

    def update_interfaces_info(self, node_id):
        node = db().query(Node).get(node_id)
        if not "interfaces" in node.meta:
            raise Exception("No interfaces metadata specified for node")

        for interface in node.meta["interfaces"]:
            interface_db = db().query(NodeNICInterface).filter_by(
                mac=interface['mac']).first()
            if interface_db:
                self.__update_existing_interface(interface_db.id, interface)
            else:
                self.__add_new_interface(node, interface)

        self.__delete_not_found_interfaces(node, node.meta["interfaces"])

    def __add_new_interface(self, node, interface_attrs):
        interface = NodeNICInterface()
        interface.node_id = node.id
        self.__set_interface_attributes(interface, interface_attrs)
        db().add(interface)
        db().commit()
        node.interfaces.append(interface)

    def __update_existing_interface(self, interface_id, interface_attrs):
        interface = db().query(NodeNICInterface).get(interface_id)
        self.__set_interface_attributes(interface, interface_attrs)
        db().commit()

    def __set_interface_attributes(self, interface, interface_attrs):
        interface.name = interface_attrs["name"]
        interface.mac = interface_attrs["mac"]

        interface.current_speed = interface_attrs.get("current_speed")
        interface.max_speed = interface_attrs.get("max_speed")

    def __delete_not_found_interfaces(self, node, interfaces):
        interfaces_mac_addresses = map(
            lambda interface: interface['mac'], interfaces)

        interfaces_to_delete = db().query(NodeNICInterface).filter(
            NodeNICInterface.node_id == node.id).filter(
                not_(NodeNICInterface.mac.in_(
                    interfaces_mac_addresses))).all()

        if interfaces_to_delete:
            mac_addresses = ' '.join(
                map(lambda i: i.mac, interfaces_to_delete))

            node_name = node.name or node.mac
            logger.info("Interfaces %s removed from node %s" % (
                mac_addresses, node_name))

            map(db().delete, interfaces_to_delete)

    def get_default_nic_networkgroups(self, node_id, nic_id):
        main_nic_id = self.get_main_nic(node_id)
        return self.get_all_cluster_networkgroups(node.id) \
            if nic_id == main_nic_id else []

    def get_all_cluster_networkgroups(self, node_id):
        node_db = db().query(Node).get(node_id)
        if node_db.cluster:
            return [ng.id for ng in node_db.cluster.network_groups]
        return []

    def get_allowed_nic_networkgroups(self, node_id, nic_id):
        """
        nic_id is not used now, but this logic will be improved
        in the future, so let it be
        """
        return self.get_all_cluster_networkgroups(node_id)

    def _get_admin_network(self, node):
        """
        Node contain mac address which sent ohai,
        when node was loaded. By this mac address
        we can identify interface name for admin network.
        """
        for interface in node.meta.get('interfaces', []):
            if interface['mac'] == node.mac:
                return {
                    'name': u'admin',
                    'dev': interface['name']}

        raise errors.CanNotFindInterface()

    def _get_interface_by_network_name(self, node_id, network_name):
        """
        Return network device which has appointed
        network with specified network name
        """
        node_db = db().query(Node).get(node_id)
        for interface in node_db.interfaces:
            for network in interface.assigned_networks:
                if network.name == network_name:
                    return interface

        raise errors.CanNotFindInterface()
