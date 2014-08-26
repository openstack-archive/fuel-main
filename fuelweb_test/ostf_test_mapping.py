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

OSTF_TEST_MAPPING = {
    'Check data replication over mysql': 'fuel_health.tests.ha.test_'
                                         'mysql_replication.'
                                         'TestMysqlReplication.'
                                         'test_mysql_replication',
    'Check amount of tables in '
    'databases is the same on each node': 'fuel_health.tests.ha.'
                                          'test_mysql_replication.'
                                          'TestMysqlReplication.'
                                          'test_os_databases',
    'Check mysql environment state': 'fuel_health.tests.ha.'
                                     'test_mysql_replication.'
                                     'TestMysqlReplication.'
                                     'test_state_of_mysql_cluster',
    'Check galera environment state': 'fuel_health.tests.ha.'
                                      'test_mysql_replication.'
                                      'TestMysqlReplication.'
                                      'test_state_of_galera_cluster',
    'Check RabbitMQ is available': 'fuel_health.tests.ha.'
                                   'test_rabbit.RabbitSmokeTest.'
                                   'test_001_rabbitmqctl_status',
    'RabbitMQ availability': 'fuel_health.tests.ha.test_rabbit.'
                             'RabbitSmokeTest.'
                             'test_002_rabbitmqctl_status_ubuntu',
    'List ceilometer availability': 'fuel_health.tests.sanity.'
                                    'test_sanity_ceilometer.'
                                    'CeilometerApiTests.test_list_meters',
    'Request instance list': 'fuel_health.tests.sanity.test_sanity_compute.'
                             'SanityComputeTest.test_list_instances',
    'Request image list': 'fuel_health.tests.sanity.test_sanity_compute.'
                          'SanityComputeTest.test_list_images',
    'Request volume list': 'fuel_health.tests.sanity.test_sanity_compute.'
                           'SanityComputeTest.test_list_volumes',
    'Request snapshot list': 'fuel_health.tests.sanity.test_sanity_compute.'
                             'SanityComputeTest.test_list_snapshots',
    'Request flavor list': 'fuel_health.tests.sanity.test_sanity_compute.'
                           'SanityComputeTest.test_list_flavors',
    'Request absolute limits list': 'fuel_health.tests.sanity.'
                                    'test_sanity_compute.SanityComputeTest.'
                                    'test_list_rate_limits',
    'Request stack list': 'fuel_health.tests.sanity.test_sanity_heat.'
                          'SanityHeatTest.test_list_stacks',
    'Request active services list': 'fuel_health.tests.sanity.'
                                    'test_sanity_identity.'
                                    'SanityIdentityTest.test_list_services',
    'Request user list': 'fuel_health.tests.sanity.test_sanity_identity.'
                         'SanityIdentityTest.test_list_users',
    'Check that required services are running': 'fuel_health.tests.sanity.'
                                                'test_sanity_infrastructure.'
                                                'SanityInfrastructureTest.'
                                                'test_001_services_state',
    'Check internet connectivity from a compute': 'fuel_health.tests.sanity.'
                                                  'test_sanity_infrastructure.'
                                                  'SanityInfrastructureTest.'
                                                  'test_002_internet_'
                                                  'connectivity_from_compute',
    'Check DNS resolution on compute node': 'fuel_health.tests.sanity.'
                                            'test_sanity_infrastructure.'
                                            'SanityInfrastructureTest.'
                                            'test_003_dns_resolution',
    'Create and delete Murano environment': 'fuel_health.tests.sanity.'
                                            'test_sanity_murano.'
                                            'MuranoSanityTests.'
                                            'test_create_and_delete_service',
    'Request list of networks': 'fuel_health.tests.sanity.'
                                'test_sanity_networking.NetworksTest.'
                                'test_list_networks',
    'Sahara tests to create/list/delete node'
    ' group and cluster templates': 'fuel_health.tests.sanity.'
                                    'test_sanity_sahara.'
                                    'SanitySaharaTests.test_sanity_sahara',
    'Create instance flavor': 'fuel_health.tests.smoke.test_create_flavor.'
                              'FlavorsAdminTest.test_create_flavor',
    'Create volume and attach it to instance': 'fuel_health.tests.smoke.'
                                               'test_create_volume.'
                                               'VolumesTest.'
                                               'test_volume_create',
    'Create keypair': 'fuel_health.tests.smoke.'
                      'test_nova_create_instance_with_connectivity.'
                      'TestNovaNetwork.test_001_create_keypairs',
    'Create security group': 'fuel_health.tests.smoke.'
                             'test_nova_create_instance_with_connectivity.'
                             'TestNovaNetwork.'
                             'test_002_create_security_groups',
    'Check network parameters': 'fuel_health.tests.smoke.'
                                'test_nova_create_instance_with_connectivity.'
                                'TestNovaNetwork.test_003_check_networks',
    'Launch instance': 'fuel_health.tests.smoke.'
                       'test_nova_create_instance_with_connectivity.'
                       'TestNovaNetwork.test_004_create_servers',
    'Check that VM is accessible '
    'via floating IP address': 'fuel_health.tests.smoke.'
                               'test_nova_create_instance_with_connectivity.'
                               'TestNovaNetwork.'
                               'test_005_check_public_network_connectivity',
    'Check network connectivity'
    ' from instance via floating IP': 'fuel_health.tests.smoke.'
                                      'test_nova_create_instance_with_'
                                      'connectivity.TestNovaNetwork.'
                                      'test_008_check_public_instance_'
                                      'connectivity_from_instance',
    'Check network connectivity from '
    'instance without floating IP': 'fuel_health.tests.smoke.test_nova_create_'
                                    'instance_with_connectivity.'
                                    'TestNovaNetwork.test_006_check_'
                                    'internet_connectivity_instance_'
                                    'without_floatingIP',
    'Launch instance, create snapshot,'
    ' launch instance from snapshot': 'fuel_health.tests.smoke.'
                                      'test_nova_image_actions.'
                                      'TestImageAction.test_snapshot',
    'Create user and authenticate with it to Horizon': 'fuel_health.tests.'
                                                       'smoke.test_'
                                                       'user_create.TestUserTe'
                                                       'nantRole.test_'
                                                       'create_user', }
