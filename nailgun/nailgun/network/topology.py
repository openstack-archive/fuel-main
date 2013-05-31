# -*- coding: utf-8 -*-

import web

from nailgun.api.models import Node
from nailgun.api.models import NetworkAssignment
from nailgun.api.models import NodeNICInterface

from nailgun.logger import logger


class TopoChecker(object):
    @classmethod
    def _is_assignment_allowed_for_node(cls, node):
        db_node = self.db.query(Node).filter_by(id=node['id']).first()
        interfaces = node['interfaces']
        db_interfaces = db_node.interfaces
        allowed_network_ids = set([n.id for n in db_node.allowed_networks])
        for iface in interfaces:
            db_iface = filter(
                lambda i: i.id == iface['id'],
                db_interfaces
            )
            db_iface = db_iface[0]
            for net in iface['assigned_networks']:
                if net['id'] not in allowed_network_ids:
                    return False
        return True

    @classmethod
    def is_assignment_allowed(cls, data):
        for node in data:
            if not cls._is_assignment_allowed_for_node(node):
                return False
        return True

    @classmethod
    def resolve_topo_conflicts(cls, data):
        raise NotImplementedError("Will be implemented later")


class NICUtils(object):

    def _update_attrs(self, node):
        db_node = self.db.query(Node).filter_by(id=node['id']).first()
        interfaces = node['interfaces']
        db_interfaces = db_node.interfaces
        for iface in interfaces:
            db_iface = filter(
                lambda i: i.id == iface['id'],
                db_interfaces
            )
            db_iface = db_iface[0]
            # Remove all old network's assignment for this interface.
            old_assignment = self.db.query(NetworkAssignment).filter_by(
                interface_id=db_iface.id,
            ).all()
            map(self.db.delete, old_assignment)
            for net in iface['assigned_networks']:
                net_assignment = NetworkAssignment()
                net_assignment.network_id = net['id']
                net_assignment.interface_id = db_iface.id
                self.db.add(net_assignment)
        return db_node

    def update_attributes(self, node):
        self.validator.verify_data_correctness(node)
        self._update_attrs(node)
        self.db.commit()

    def update_collection_attributes(self, data):
        updated_nodes = []
        for node in data:
            self.validator.verify_data_correctness(node)
            db_node = self._update_attrs(node)
            updated_nodes.append(db_node)
        self.db.commit()
        return updated_nodes

    def get_main_nic(self, node):
        for nic in node.interfaces:
            if node.mac == nic.mac:
                return nic
        if node.interfaces:
            return node.interfaces[0]

    def get_all_cluster_networkgroups(self, node):
        if node.cluster:
            return node.cluster.network_groups
        return []

    def get_default_nic_networkgroups(self, node, nic):
        main_nic = self.get_main_nic(node)
        return self.get_all_cluster_networkgroups(node) \
            if nic.id == main_nic.id else []

    def get_allowed_nic_networkgroups(self, node, nic):
        return self.get_all_cluster_networkgroups(node)

    def allow_network_assignment_to_all_interfaces(self, node):
        """
        Add all network groups from cluster
        to allowed_networks list for all interfaces
        of specified node
        """
        for nic in node.interfaces:
            for net_group in self.get_all_cluster_networkgroups(node):
                nic.allowed_networks.append(net_group)

    def clear_assigned_networks(self, node):
        for nic in node.interfaces:
            while nic.assigned_networks:
                nic.assigned_networks.pop()

    def clear_all_allowed_networks(self, node):
        for nic in node.interfaces:
            while nic.allowed_networks:
                nic.allowed_networks.pop()

    def assign_networks_to_main_interface(self, node):
        self.clear_assigned_networks(node)
        main_nic = self.get_main_nic(node)
        if main_nic:
            for net_group in self.get_all_cluster_networkgroups(node):
                main_nic.assigned_networks.append(net_group)
