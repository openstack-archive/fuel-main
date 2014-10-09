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


from proboscis.asserts import assert_equal
from random import randrange

from fuelweb_test import logwrap
from fuelweb_test import logger
from fuelweb_test.settings import OPENSTACK_RELEASE
from fuelweb_test.settings import OPENSTACK_RELEASE_UBUNTU


class SecurityChecks(object):

    def __init__(self, nailgun_client, environment):
        self.client = nailgun_client
        self.environment = environment
        super(SecurityChecks, self).__init__()

    @logwrap
    def _listen_random_port(self, ip_address, protocol, tmp_file_path):
        remote = self.environment.get_ssh_to_remote(ip_address)
        # Install socat
        if OPENSTACK_RELEASE_UBUNTU in OPENSTACK_RELEASE:
            cmd = '/usr/bin/apt-get install -y {pkg}'.format(pkg='socat')
        else:
            cmd = '/usr/bin/yum install -y {pkg}'.format(pkg='socat')
        result = remote.execute(cmd)
        if not result['exit_code'] == 0:
            raise Exception('Could not install package: {0}\n{1}'.
                            format(result['stdout'], result['stderr']))
        # Get all used ports
        cmd = ('netstat -A inet -ln --{proto} | awk \'$4 ~ /^({ip}'
               '|0\.0\.0\.0):[0-9]+/ {{split($4,port,":"); print '
               'port[2]}}\'').format(ip=ip_address, proto=protocol)

        used_ports = [int(p.strip()) for p in remote.execute(cmd)['stdout']]

        # Get list of opened ports
        cmd = ('iptables -t filter -S INPUT | sed -rn -e \'s/^.*\s\-p\s+'
               '{proto}\s.*\-\-(dport|ports|dports)\s+([0-9,\,,:]+)\s.*'
               '-j\s+ACCEPT.*$/\\2/p\' | sed -r \'s/,/\\n/g; s/:/ /g\' |'
               ' while read ports; do if [[ "$ports" =~ [[:digit:]]'
               '[[:blank:]][[:digit:]] ]]; then seq $ports; else echo '
               '"$ports";fi; done').format(proto=protocol)

        allowed_ports = [int(p.strip()) for p in remote.execute(cmd)['stdout']]

        test_port = randrange(10000)
        while test_port in used_ports or test_port in allowed_ports:
            test_port = randrange(10000)

        # Create dump of iptables rules
        cmd = 'iptables-save > {0}.dump'.format(tmp_file_path)
        result = remote.execute(cmd)
        assert_equal(result['exit_code'], 0,
                     'Dumping of iptables rules failed on {0}: {1}; {2}'.
                     format(ip_address, result['stdout'], result['stderr']))

        # Start listening for connections on test_port
        cmd = ('socat {proto}4-LISTEN:{port},bind={ip} {file} '
               '&>/dev/null & pid=$! ; disown; sleep 1; kill -0 $pid').\
            format(proto=protocol, ip=ip_address, file=tmp_file_path,
                   port=test_port)
        result = remote.execute(cmd)
        assert_equal(result['exit_code'], 0,
                     'Listening on {0}:{1}/{2} port failed: {3}'.
                     format(ip_address, test_port, protocol,
                            result['stderr']))
        return test_port

    @logwrap
    def verify_firewall(self, cluster_id):
        admin_remote = self.environment.get_admin_remote()
        # Install NetCat
        if not self.environment.admin_install_pkg('nc') == 0:
            raise Exception('Can not install package "nc".')

        cluster_nodes = self.client.list_cluster_nodes(cluster_id)
        tmp_file_path = '/var/tmp/iptables_check_file'
        check_string = 'FirewallHole'

        for node in cluster_nodes:
            protocols_to_check = ['tcp', 'udp']
            for protocol in protocols_to_check:
                port = self._listen_random_port(ip_address=node['ip'],
                                                protocol=protocol,
                                                tmp_file_path=tmp_file_path)
                nc_opts = ''
                if protocol == 'udp':
                    nc_opts = '{} -u'.format(nc_opts)

                cmd = 'echo {string} | nc {opts} {ip} {port}'.\
                    format(opts=nc_opts, string=check_string, ip=node['ip'],
                           port=port)
                admin_remote.execute(cmd)
                remote = self.environment.get_ssh_to_remote(node['ip'])
                cmd = 'cat {0}; mv {0}{{,.old}}'.format(tmp_file_path)
                result = remote.execute(cmd)
                if ''.join(result['stdout']).strip() == check_string:
                    raise Exception(('Firewall vulnerability detected. '
                                    'Unused port {0}/{1} can be accessed'
                                    ' on {2} (node-{3}) node. Check {4}.old'
                                    ' and {4}.dump files on the node for de'
                                    'tails').format(port, protocol,
                                                    node['name'], node['id'],
                                                    tmp_file_path))
        logger.info('Firewall test passed')
