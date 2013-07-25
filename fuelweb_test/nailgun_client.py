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


import logging
from fuelweb_test.helpers import HTTPClient
from fuelweb_test.integration.decorators import debug, json_parse


logger = logging.getLogger(__name__)
logwrap = debug(logger)


class NailgunClient(object):
    def __init__(self, ip):
        self.client = HTTPClient(url="http://%s:8000" % ip)
        super(NailgunClient, self).__init__()

    @logwrap
    def get_root(self):
        return self.client.get("/")

    @logwrap
    @json_parse
    def list_nodes(self):
        return self.client.get("/api/nodes/")

    @logwrap
    @json_parse
    def list_cluster_nodes(self, cluster_id):
        return self.client.get("/api/nodes/?cluster_id=%s" % cluster_id)

    @logwrap
    @json_parse
    def get_networks(self, cluster_id):
        return self.client.get(
            "/api/clusters/%d/network_configuration/" % cluster_id)

    @logwrap
    @json_parse
    def verify_networks(self, cluster_id, networks):
        return self.client.put(
            "/api/clusters/%d/network_configuration/verify/" % cluster_id,
            {'networks': networks}
        )

    @logwrap
    @json_parse
    def get_cluster_attributes(self, cluster_id):
        return self.client.get(
            "/api/clusters/%s/attributes/" % cluster_id
        )

    @logwrap
    @json_parse
    def update_cluster_attributes(self, cluster_id, attrs):
        return self.client.put(
            "/api/clusters/%s/attributes/" % cluster_id, attrs
        )

    @logwrap
    @json_parse
    def get_cluster(self, cluster_id):
        return self.client.get(
            "/api/clusters/%s" % cluster_id)

    @logwrap
    @json_parse
    def update_cluster(self, cluster_id, data):
        return self.client.put(
            "/api/clusters/%s/" % cluster_id,
            data
        )

    @logwrap
    @json_parse
    def delete_cluster(self, cluster_id):
        return self.client.delete(
            "/api/clusters/%s/" % cluster_id
        )

    @logwrap
    @json_parse
    def update_node(self, node_id, data):
        return self.client.put(
            "/api/nodes/%s/" % node_id, data
        )

    @logwrap
    @json_parse
    def update_nodes(self, data):
        return self.client.put(
            "/api/nodes", data
        )

    @logwrap
    @json_parse
    def deploy_cluster_changes(self, cluster_id):
        return self.client.put(
            "/api/clusters/%d/changes/" % cluster_id
        )

    @logwrap
    @json_parse
    def get_task(self, task_id):
        return self.client.get("/api/tasks/%s" % task_id)

    @logwrap
    @json_parse
    def get_releases(self):
        return self.client.get("/api/releases/")

    @logwrap
    @json_parse
    def get_node_disks(self, disk_id):
        return self.client.get("/api/nodes/%s/disks" % disk_id)

    @logwrap
    def get_grizzly_release_id(self):
        for release in self.get_releases():
            if release["name"].find("Grizzly") != -1:
                return release["id"]

    @logwrap
    @json_parse
    def get_node_interfaces(self, node_id):
        return self.client.get("api/nodes/%s/interfaces" % node_id)

    @logwrap
    @json_parse
    def put_node_interfaces(self, data):
        return self.client.put("api/nodes/interfaces", data)

    @logwrap
    @json_parse
    def list_clusters(self):
        return self.client.get("/api/clusters/")

    @logwrap
    @json_parse
    def create_cluster(self, data):
        return self.client.post(
            "/api/clusters",
            data=data
        )

    @logwrap
    @json_parse
    def get_ostf_test_sets(self):
        return self.client.get("/ostf/testsets")

    @logwrap
    @json_parse
    def get_ostf_tests(self):
        return self.client.get("/ostf/tests")

    @logwrap
    @json_parse
    def get_ostf_test_run(self, cluster_id):
        return self.client.get("/ostf/testruns/last/%s" % cluster_id)

    @logwrap
    @json_parse
    def ostf_run_tests(self, cluster_id, test_sets_list):
        data = []
        for test_set in test_sets_list:
            data.append(
                {
                    'metadata': {'cluster_id': cluster_id, 'config': {}},
                    'testset': test_set
                }
            )
        return self.client.post("/ostf/testruns", data)

    @logwrap
    @json_parse
    def update_network(self, cluster_id, networks=None, net_manager=None):
        data = {}
        if networks is not None:
            data.update({'networks': networks})
        if net_manager is not None:
            data.update({'net_manager': net_manager})
        return self.client.put(
            "/api/clusters/%d/network_configuration" % cluster_id, data
        )

    @logwrap
    def get_cluster_id(self, name):
        for cluster in self.list_clusters():
            if cluster["name"] == name:
                return cluster["id"]

    @logwrap
    def add_syslog_server(self, cluster_id, host, port):
        # Here we updating cluster editable attributes
        # In particular we set extra syslog server
        attributes = self.get_cluster_attributes(cluster_id)
        attributes["editable"]["syslog"]["syslog_server"]["value"] = host
        attributes["editable"]["syslog"]["syslog_port"]["value"] = port
        self.update_cluster_attributes(cluster_id, attributes)

    @logwrap
    def clean_clusters(self):
        for cluster in self.list_clusters():
            self.delete_cluster(cluster["id"])

    @logwrap
    def _get_cluster_vlans(self, cluster_id):
        cluster_vlans = []
        for network in self.get_networks(cluster_id)['networks']:
            amount = network.get('amount', 1)
            cluster_vlans.extend(range(network['vlan_start'],
                                       network['vlan_start'] + amount))
        return cluster_vlans

    @logwrap
    @json_parse
    def get_notifications(self):
        return self.client.get("/api/notifications")
