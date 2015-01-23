#    Copyright 2014 Mirantis, Inc.
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

from proboscis import SkipTest
from proboscis import test
from proboscis.asserts import assert_equal

from fuelweb_test.helpers.decorators import check_fuel_statistics
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.settings import MULTIPLE_NETWORKS
from fuelweb_test.settings import NODEGROUPS
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test.tests.base_test_case import SetupEnvironment


@test(groups=["multiple_cluster_networks", "thread_7"])
class TestMultipleClusterNets(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["multiple_cluster_networks", "multiple_cluster_net_setup"])
    @log_snapshot_on_error
    def multiple_cluster_net_setup(self):
        """Check master node deployment and configuration with 2 sets of nets

        Scenario:
            1. Revert snapshot with 5 slaves
            2. Check that slaves got IPs via DHCP from both admin/pxe networks
            3. Make environment snapshot
        Duration 6m
        Snapshot multiple_cluster_net_setup

        """

        if not MULTIPLE_NETWORKS:
            raise SkipTest()
        self.env.revert_snapshot("ready_with_5_slaves")

        # Get network parts of IP addresses with /24 netmask
        networks = ['.'.join(self.env._get_network(n).split('.')[0:-1]) for n
                    in [self.env.admin_net, self.env.admin_net2]]
        nodes_addresses = ['.'.join(node['ip'].split('.')[0:-1]) for node in
                           self.fuel_web.client.list_nodes()]

        assert_equal(set(networks), set(nodes_addresses),
                     "Only one admin network is used for discovering slaves:"
                     " '{0}'".format(set(nodes_addresses)))

        self.env.make_snapshot("multiple_cluster_net_setup", is_make=True)

    @test(depends_on=[multiple_cluster_net_setup],
          groups=["multiple_cluster_networks",
                  "multiple_cluster_net_neutron_gre_ha", "thread_7"])
    @log_snapshot_on_error
    @check_fuel_statistics
    def deploy_neutron_gre_ha_nodegroups(self):
        """Deploy HA environment with NeutronGRE and 2 nodegroups

        Scenario:
            1. Revert snapshot with 2 networks sets for slaves
            2. Create cluster (HA) with Neutron GRE
            3. Add 3 controller nodes from default nodegroup
            4. Add 2 compute nodes from custom nodegroup
            5. Deploy cluster
            6. Run health checks (OSTF)

        Duration 110m
        Snapshot deploy_neutron_gre_ha_nodegroups

        """

        if not MULTIPLE_NETWORKS:
            raise SkipTest()
        self.env.revert_snapshot("multiple_cluster_net_setup")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": 'gre',
                'tenant': 'haGre',
                'user': 'haGre',
                'password': 'haGre'
            }
        )

        nodegroup1 = NODEGROUPS[0]['name']
        nodegroup2 = NODEGROUPS[1]['name']

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': [['controller'], nodegroup1],
                'slave-05': [['controller'], nodegroup1],
                'slave-03': [['controller'], nodegroup1],
                'slave-02': [['compute', 'cinder'], nodegroup2],
                'slave-04': [['compute', 'cinder'], nodegroup2],
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("deploy_neutron_gre_ha_nodegroups")

    @test(depends_on=[multiple_cluster_net_setup],
          groups=["multiple_cluster_networks",
                  "multiple_cluster_net_ceph_ha", "thread_7"])
    @log_snapshot_on_error
    def deploy_ceph_ha_nodegroups(self):
        """Deploy HA environment with NeutronGRE, Ceph and 2 nodegroups

        Scenario:
            1. Revert snapshot with 2 networks sets for slaves
            2. Create cluster (HA) with Neutron GRE and Ceph
            3. Add 3 controller + ceph nodes from default nodegroup
            4. Add 2 compute + ceph nodes from custom nodegroup
            5. Deploy cluster
            6. Run health checks (OSTF)

        Duration 110m
        Snapshot deploy_neutron_gre_ha_nodegroups

        """

        if not MULTIPLE_NETWORKS:
            raise SkipTest()
        self.env.revert_snapshot("multiple_cluster_net_setup")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings={
                'volumes_ceph': True,
                'images_ceph': True,
                'volumes_lvm': False,
                "net_provider": 'neutron',
                "net_segment_type": 'gre',
                'tenant': 'haGreCeph',
                'user': 'haGreCeph',
                'password': 'haGreCeph'
            }
        )

        nodegroup1 = NODEGROUPS[0]['name']
        nodegroup2 = NODEGROUPS[1]['name']

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': [['controller', 'ceph-osd'], nodegroup1],
                'slave-05': [['controller', 'ceph-osd'], nodegroup1],
                'slave-03': [['controller', 'ceph-osd'], nodegroup1],
                'slave-02': [['compute', 'ceph-osd'], nodegroup2],
                'slave-04': [['compute', 'ceph-osd'], nodegroup2],
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("deploy_neutron_gre_ha_nodegroups")
