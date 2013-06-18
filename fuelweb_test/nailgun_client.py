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
    def update_node(self, node_id, data):
        return self.client.put(
            "/api/nodes/%s/" % node_id, data
        )

    @logwrap
    @json_parse
    def update_cluster_changes(self, cluster_id):
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
    def get_grizzly_release_id(self):
        for release in self.get_releases():
            if release["name"] == "Grizzly":
                return release["id"]

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
    def update_network(self, cluster_id, flat_net=None, net_manager=None):
        data = {}
        if flat_net is not None:
            data.update({'networks': flat_net})
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
            self.update_cluster(
                cluster["id"], {"nodes": []}
            )

    @logwrap
    def _get_cluster_vlans(self, cluster_id):
        cluster_vlans = []
        for network in self.get_networks(cluster_id)['networks']:
            amount = network.get('amount', 1)
            cluster_vlans.extend(range(network['vlan_start'],
                                       network['vlan_start'] + amount))
        return cluster_vlans
