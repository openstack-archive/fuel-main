import logging
from datetime import datetime
from devops.helpers.helpers import wait
from nose.tools import assert_equals
from proboscis import test, before_class, after_class, factory
from proboscis.asserts import assert_true
from fuelweb_test.helpers import logwrap
from fuelweb_test.integration.ci_fuel_web import CiFuelWeb
from fuelweb_test.nailgun_client import NailgunClient
from testdata import TestParamsList


#logging.basicConfig(
#    format=':%(lineno)d: %(asctime)s %(message)s',
#    level=logging.DEBUG
#)

logger = logging.getLogger(__name__)

@factory
def test_deploy_factory():

    tests = list()
    for testdata in TestParamsList():
        td = TestDeploy()
        td.env = testdata['env']
        td.nodes = testdata['nodes']
        td.interfaces = testdata['interfaces']
        td.env_attributes = testdata['env_attributes']
        td.network_conf = testdata['network_conf']
        tests.append(td)
    return tests


@test(groups=['simple_deploy'])
class TestDeploy(object):

    def __init__(self, name=None):
        self.name = name or "TEST_%s" % datetime.now()

        self.ci = CiFuelWeb()

        admin_node_ip = self.ci.nodes().admin.get_ip_address_by_network_name('internal')
        self.client = NailgunClient(admin_node_ip)

        # settings will be injected in factory method
        self.env = {}
        self.nodes = {}
        self.interfaces = {}
        self.env_attributes = {}
        self.network_conf = {}

    @test
    def deploy_environment(self):
        self.ci.get_empty_environment()

        # create environment
        self.env['release'] = self.client.get_release_id(self.env['release'])
        self.env['name'] = self.env['name'] or self.name

        self.env = self.client.create_cluster(data=self.env)

        # add nodes
        self.bootstrap_nodes(self.devops_nodes_by_names(self.nodes.keys()))
        self.nodes = self.update_nodes(self.env['id'], self.nodes)

        # update node's interfaces
        for node in self.nodes:
            self.update_node_networks(node['id'], self.interfaces)

        # update environment attributes
        attributes = self.client.get_cluster_attributes(self.env['id'])
        attributes = self._update_dict(attributes, self.env_attributes)
        self.client.update_cluster_attributes(self.env['id'], attributes)

        # update environment networks
        networks = self.client.get_networks(self.env['id'])

        for net_conf in self.network_conf['networks']:
            for net in networks['networks']:
                if net["name"] == net_conf['name']:
                    net.update(net_conf)
                    break

        if self.env['net_provider'] == 'neutron' and 'neutron_parameters' in self.network_conf:
            networks['neutron_parameters'].update(self.network_conf['neutron_parameters'])

        self.client.client.put(
            "/api/clusters/%d/network_configuration/%s" %
            (self.env['id'], self.env['net_provider']), networks
        )

        # deploy changes
        task = self.client.deploy_cluster_changes(self.env['id'])
        assert_equals('ready', self._task_wait(task, 90 * 60)['status'])

        self.ci.snapshot_state(self.name)

    # Help methods
    @logwrap
    def bootstrap_nodes(self, devops_nodes, timeout=600):
        """Start vms and wait they are registered on nailgun.
        :rtype : List of registred nailgun nodes
        """
        for node in devops_nodes:
            node.start()
        wait(lambda: all(self.nailgun_nodes(devops_nodes)), 15, timeout)
        return self.nailgun_nodes(devops_nodes)

    @logwrap
    def update_nodes(self, cluster_id, nodes_dict,
                     pending_addition=True, pending_deletion=False):
        # update nodes in cluster
        nodes_data = []
        for node_name in nodes_dict:
            devops_node = self.ci.environment().node_by_name(node_name)
            node = self.get_node_by_devops_node(devops_node)
            node_data = {'cluster_id': cluster_id, 'id': node['id'],
                         'pending_addition': pending_addition,
                         'pending_deletion': pending_deletion,
                         'pending_roles': nodes_dict[node_name],
                         'name': '%s_%s' % (self.ci.environment().name,
                                            devops_node.name)}
            nodes_data.append(node_data)

        # assume nodes are going to be updated for one cluster only
        node_ids = [str(node_info['id']) for node_info in nodes_data]
        self.client.update_nodes(nodes_data)

        nailgun_nodes = self.client.list_cluster_nodes(cluster_id)
        cluster_node_ids = map(lambda node: str(node['id']), nailgun_nodes)
        assert_true(
            all([node_id in cluster_node_ids for node_id in node_ids]))
        return nailgun_nodes

    def devops_nodes_by_names(self, devops_node_names):
        return map(lambda name: self.ci.environment().node_by_name(name),
                   devops_node_names)

    def nailgun_nodes(self, devops_nodes):
        return map(lambda node: self.get_node_by_devops_node(node),
                   devops_nodes)

    @logwrap
    def get_node_by_devops_node(self, devops_node):
        """Returns dict with nailgun slave node description if node is
        registered. Otherwise return None.
        """
        mac_addresses = map(
            lambda interface: interface.mac_address.capitalize(),
            devops_node.interfaces)
        for nailgun_node in self.client.list_nodes():
            if nailgun_node['mac'].capitalize() in mac_addresses:
                nailgun_node['devops_name'] = devops_node.name
                return nailgun_node
        return None

    @logwrap
    def update_node_networks(self, node_id, interfaces_dict):
        interfaces = self.client.get_node_interfaces(node_id)
        for interface in interfaces:
            interface_name = interface['name']
            interface['assigned_networks'] = []
            for allowed_network in interface['allowed_networks']:
                key_exists = interface_name in interfaces_dict
                if key_exists and \
                        allowed_network['name'] \
                        in interfaces_dict[interface_name]:
                    interface['assigned_networks'].append(allowed_network)

        self.client.put_node_interfaces(
            [{'id': node_id, 'interfaces': interfaces}])

    @logwrap
    def _task_wait(self, task, timeout):
        wait(
            lambda: self.client.get_task(
                task['id'])['status'] != 'running',
            timeout=timeout)
        return self.client.get_task(task['id'])

    def _update_dict(self, target, source):
        def values_are_dicts(dictionary):
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    return True
            return False

        for key, value in target.items():
            if key in source:
                if isinstance(value, unicode) or isinstance(value, str) or isinstance(value, list):
                    target[key] = source[key]
                    continue

                if values_are_dicts(value):
                    target[key] = self._update_dict(target[key], source[key])
                else:
                    target[key].update(source[key])
        return target


