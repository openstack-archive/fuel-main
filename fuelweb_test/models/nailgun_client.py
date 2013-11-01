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

from fuelweb_test.settings import OPENSTACK_RELEASE
from fuelweb_test.helpers.decorators import debug, json_parse
from fuelweb_test.helpers.http import HTTPClient


logger = logging.getLogger(__name__)
logwrap = debug(logger)


class NailgunClient(object):
    def __init__(self, admin_node_ip):
        self.client = HTTPClient(url="http://{}:8000".format(admin_node_ip))
        super(NailgunClient, self).__init__()

    @logwrap
    def get_root(self):
        return self.client.get("/")

    @json_parse
    def list_nodes(self):
        return self.client.get("/api/nodes/")

    @json_parse
    def list_cluster_nodes(self, cluster_id):
        return self.client.get("/api/nodes/?cluster_id={}".format(cluster_id))

    @logwrap
    @json_parse
    def get_networks(self, cluster_id):
        net_provider = self.get_cluster(cluster_id)['net_provider']
        return self.client.get(
            "/api/clusters/{}/network_configuration/{}".format(
                cluster_id, net_provider
            )
        )

    @logwrap
    @json_parse
    def verify_networks(self, cluster_id, networks):
        net_provider = self.get_cluster(cluster_id)['net_provider']
        return self.client.put(
            "/api/clusters/{}/network_configuration/{}/verify/".format(
                cluster_id, net_provider
            ),
            {
                'networks': networks
            }
        )

    @json_parse
    def get_cluster_attributes(self, cluster_id):
        return self.client.get(
            "/api/clusters/{}/attributes/".format(cluster_id)
        )

    @logwrap
    @json_parse
    def update_cluster_attributes(self, cluster_id, attrs):
        return self.client.put(
            "/api/clusters/{}/attributes/".format(cluster_id),
            attrs
        )

    @logwrap
    @json_parse
    def get_cluster(self, cluster_id):
        return self.client.get(
            "/api/clusters/{}".format(cluster_id)
        )

    @logwrap
    @json_parse
    def update_cluster(self, cluster_id, data):
        return self.client.put(
            "/api/clusters/{}/".format(cluster_id),
            data
        )

    @logwrap
    @json_parse
    def delete_cluster(self, cluster_id):
        return self.client.delete(
            "/api/clusters/{}/".format(cluster_id)
        )

    @json_parse
    def update_node(self, node_id, data):
        return self.client.put(
            "/api/nodes/{}/".format(node_id), data
        )

    @json_parse
    def update_nodes(self, data):
        return self.client.put(
            "/api/nodes", data
        )

    @logwrap
    @json_parse
    def deploy_cluster_changes(self, cluster_id):
        return self.client.put(
            "/api/clusters/{}/changes/".format(cluster_id)
        )

    @logwrap
    @json_parse
    def get_task(self, task_id):
        return self.client.get("/api/tasks/{}".format(task_id))

    @logwrap
    @json_parse
    def get_tasks(self):
        return self.client.get("/api/tasks")

    @logwrap
    @json_parse
    def get_releases(self):
        return self.client.get("/api/releases/")

    @logwrap
    @json_parse
    def get_node_disks(self, disk_id):
        return self.client.get("/api/nodes/{}/disks".format(disk_id))

    @logwrap
    def get_release_id(self, release_name=OPENSTACK_RELEASE):
        for release in self.get_releases():
            if release["name"].find(release_name) != -1:
                return release["id"]

    @logwrap
    @json_parse
    def get_node_interfaces(self, node_id):
        return self.client.get("/api/nodes/{}/interfaces".format(node_id))

    @logwrap
    @json_parse
    def put_node_interfaces(self, data):
        return self.client.put("/api/nodes/interfaces", data)

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
    def get_ostf_test_sets(self, cluster_id):
        return self.client.get("/ostf/testsets/{}".format(cluster_id))

    @json_parse
    def get_ostf_tests(self, cluster_id):
        return self.client.get("/ostf/tests/{}".format(cluster_id))

    @json_parse
    def get_ostf_test_run(self, cluster_id):
        return self.client.get("/ostf/testruns/last/{}".format(cluster_id))

    @logwrap
    @json_parse
    def ostf_run_tests(self, cluster_id, test_sets_list):
        data = []
        for test_set in test_sets_list:
            data.append(
                {
                    'metadata': {'cluster_id': str(cluster_id), 'config': {}},
                    'testset': test_set
                }
            )
        # get tests otherwise 500 error will be thrown
        self.get_ostf_tests(cluster_id)
        return self.client.post("/ostf/testruns", data)

    @logwrap
    @json_parse
    def update_network(self, cluster_id, networks=None, net_manager=None):
        data = {}
        net_provider = self.get_cluster(cluster_id)['net_provider']
        if networks is not None:
            data.update({'networks': networks})
        if net_manager is not None:
            data.update({'net_manager': net_manager})
        return self.client.put(
            "/api/clusters/{}/network_configuration/{}".format(
                cluster_id, net_provider
            ),
            data
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
    def get_cluster_vlans(self, cluster_id):
        cluster_vlans = []
        for network in self.get_networks(cluster_id)['networks']:
            if not network['vlan_start'] is None:
                amount = network.get('amount', 1)
                cluster_vlans.extend(range(network['vlan_start'],
                                           network['vlan_start'] + amount))
        return cluster_vlans

    @logwrap
    @json_parse
    def get_notifications(self):
        return self.client.get("/api/notifications")

    @logwrap
    @json_parse
    def update_redhat_setup(self, data):
        return self.client.post("/api/redhat/setup", data=data)

    @logwrap
    @json_parse
    def generate_logs(self):
        return self.client.put("/api/logs/package")
