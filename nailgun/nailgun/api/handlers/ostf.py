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


import web
import traceback

from nailgun.db import db
from nailgun.logger import logger
from nailgun.api.handlers.base import JSONHandler, content_json
from nailgun.api.models import Cluster, Network, NetworkGroup, IPAddr
from nailgun.network.manager import NetworkManager


class OSTFHandler(JSONHandler):
    """
    Handler for openstack testing framework
    https://github.com/Mirantis/fuel-ostf-plugin
    will be removed in the next release, because
    plugin itself should request all data from
    nailgun
    """

    @content_json
    def GET(self, cluster_id):
        try:
            cluster = db().query(Cluster).get(cluster_id)
            cluster_attrs = self.get_cluster_attrs(cluster)
            network_manager = NetworkManager()
            horizon_url = network_manager.get_horizon_url(cluster_id)
            keystone_url = network_manager.get_keystone_url(cluster_id)

            return {
                'horizon_url': horizon_url,
                'keystone_url': keystone_url,
                'admin_username': cluster_attrs['user'],
                'admin_password': cluster_attrs['password'],
                'admin_tenant_name': cluster_attrs['tenant'],
                'controller_nodes_ips': self.get_controller_nodes_ips(cluster),
                'controller_nodes_names': self.get_controller_nodes_fqdns(
                    cluster),
            }
        except Exception as exc:
            logger.error(traceback.format_exc())
            raise web.badrequest(message=str(exc))

    def get_cluster_attrs(self, cluster):
        attrs = cluster.attributes.editable
        return {
            'user': attrs['access']['user']['value'],
            'password': attrs['access']['password']['value'],
            'tenant': attrs['access']['tenant']['value'],
        }

    def get_controller_nodes_fqdns(self, cluster):
        return sorted([node.fqdn for node in self.controllers(cluster)])

    def get_controller_nodes_ips(self, cluster):
        '''
        Return admin network ips
        '''
        network_manager = NetworkManager()
        admin_net_id = network_manager.get_admin_network_id()
        ip_addrs = []
        for node in self.controllers(cluster):
            ip_addr = db().query(IPAddr).filter_by(
                node=node.id, network=admin_net_id).first().ip_addr
            ip_addrs.append(ip_addr)

        return ip_addrs

    def controllers(self, cluster):
        return filter(lambda node: node.role == 'controller', cluster.nodes)
