import logging
from proboscis import test, factory
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment
from fuelweb_test.tests.ddt.gtestdata import TestParamsList


#logging.basicConfig(
#    format=':%(lineno)d: %(asctime)s %(message)s',
#    level=logging.DEBUG
#)

logger = logging.getLogger(__name__)

@factory
def test_deploy_factory():
    return [TestDeploy(test_params) for test_params in TestParamsList()]


@test(groups=['ddt'])
class TestDeploy(TestBasic):

    def __init__(self, params):
        super(TestDeploy, self).__init__()
        self.params = params

    @test(depends_on=[SetupEnvironment.prepare_release])
    @log_snapshot_on_error
    def deploy_environment(self):
        logger.info(self.params)

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(
            self.env.devops_nodes_by_names(self.params.nodes.keys()))

        cluster_id = self.fuel_web.create_cluster(
            name=self.params.environment['name'],
            release_name=self.params.environment['release'],
            mode=self.params.environment['mode'],
            settings=self.params.environment['settings']
        )
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        nailgun_nodes = \
            self.fuel_web.update_nodes(cluster_id,  self.params.nodes)

        # update node's interfaces
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(
                node['id'], self.params.interfaces)

        # update environment attributes
        attributes = self.fuel_web.client.get_cluster_attributes(cluster_id)
        attributes = self._update_dict(attributes, self.params.settings)
        self.fuel_web.client.update_cluster_attributes(cluster_id, attributes)

        # update environment networks
        networks = self.fuel_web.client.get_networks(cluster_id)

        for net_conf in self.params.networks['networks']:
            for net in networks['networks']:
                if net["name"] == net_conf['name']:
                    net.update(net_conf)
                    break

        if 'neutron_parameters' in self.params.networks:
            networks['neutron_parameters'].update(
                self.params.networks['neutron_parameters'])

        self.fuel_web.client.client.put(
            "/api/clusters/%d/network_configuration/%s" %
            (cluster_id, cluster['net_provider']), networks
        )

        # deploy changes
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.env.make_snapshot(self.params.environment['name'])

    # Help methods
    def _update_dict(self, target, source):
        """
            Updates nested dictionary values.
        """
        def values_are_dicts(dictionary):
            for v in dictionary.values():
                if isinstance(v, dict):
                    return True
            return False

        for key, value in target.items():
            if key in source:
                is_unicode = isinstance(value, unicode)
                is_string = isinstance(value, str)
                is_list = isinstance(value, list)
                if is_unicode or is_string or is_list:
                    target[key] = source[key]
                    continue

                if values_are_dicts(value):
                    target[key] = self._update_dict(target[key], source[key])
                else:
                    target[key].update(source[key])
        return target


