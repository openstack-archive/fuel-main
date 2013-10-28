import logging
from datetime import datetime
from proboscis import test, factory
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment
from fuelweb_test.tests.ddt.testdata import TestParamsList


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
        td.environment = testdata['env']
        td.nodes = testdata['nodes']
        td.interfaces = testdata['interfaces']
        td.env_attributes = testdata['env_attributes']
        td.network_conf = testdata['network_conf']
        tests.append(td)
    return tests


@test(groups=['ddt'])
class TestDeploy(TestBasic):

    def __init__(self, name=None):
        super(TestDeploy, self).__init__()

        self.name = name or "TEST_%s" % datetime.now()

        # settings will be injected in factory method
        self.environment = {}
        self.nodes = {}
        self.interfaces = {}
        self.env_attributes = {}
        self.network_conf = {}

    @test(depends_on=[SetupEnvironment.prepare_release])
    @log_snapshot_on_error
    def deploy_environment(self):
        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.devops_nodes_by_names(self.nodes.keys()))

        cluster_id = self.fuel_web.create_cluster(
            name=self.name,
            release_name=self.environment['release'],
            mode=self.environment['mode'],
            settings=self.environment['settings']
        )
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        nailgun_nodes = self.fuel_web.update_nodes(cluster_id,  self.nodes)

        # update node's interfaces
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(node['id'], self.interfaces)

        # update environment attributes
        attributes = self.fuel_web.client.get_cluster_attributes(cluster_id)
        attributes = self._update_dict(attributes, self.env_attributes)
        self.fuel_web.client.update_cluster_attributes(cluster_id, attributes)

        # update environment networks
        networks = self.fuel_web.client.get_networks(cluster_id)

        for net_conf in self.network_conf['networks']:
            for net in networks['networks']:
                if net["name"] == net_conf['name']:
                    net.update(net_conf)
                    break

        if 'neutron_parameters' in self.network_conf:
            networks['neutron_parameters'].update(self.network_conf['neutron_parameters'])

        self.fuel_web.client.client.put(
            "/api/clusters/%d/network_configuration/%s" %
            (cluster_id, cluster['net_provider']), networks
        )

        # deploy changes
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.env.make_snapshot(self.name)

    # Help methods
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


