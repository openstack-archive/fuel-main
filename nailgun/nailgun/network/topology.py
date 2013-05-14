# -*- coding: utf-8 -*-

import web

from nailgun.api.models import Node
from nailgun.api.models import NetworkGroup
from nailgun.api.models import NetworkAssignment
from nailgun.api.models import NodeNICInterface


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
            NetworkAssignment.verify_data_correctness(node)
            if not cls._is_assignment_allowed_for_node(node):
                return False
        return True

    @classmethod
    def resolve_topo_conflicts(cls, data):
        raise NotImplementedError("Will be implemented later")


class NICUtils(object):
    def get_nics_from_meta(self, node):
        nics = []
        if node.meta and node.meta.get('interfaces'):
            for i in node.meta['interfaces']:
                if 'name' not in i or 'mac' not in i:
                    logger.debug('Some node NIC interface in "meta" doesn\'t'
                                ' have name or mac')
                    continue
                nic = NodeNICInterface()
                nic.node_id = node.id
                for key in ('name', 'mac', 'current_speed', 'max_speed'):
                    if key in i:
                        setattr(nic, key, i[key])
                # Skip duplicated interfaces.
                if filter(lambda k: k.mac == nic.mac, nics):
                    logger.debug('Duplicated interface with MAC %r for node %r'
                                ' (id: %s)',
                                nic.mac, node.name, node.id)
                    continue
                nics.append(nic)
        return nics