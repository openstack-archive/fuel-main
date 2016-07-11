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

import time
import yaml

from devops.helpers.helpers import _tcp_ping
from devops.helpers.helpers import _wait
from devops.helpers.helpers import SSHClient
from devops.helpers.helpers import wait
from devops.helpers.ntp import sync_time
from devops.models import Environment
from ipaddr import IPNetwork
from keystoneclient import exceptions
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_true

from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import revert_info
from fuelweb_test.helpers.decorators import retry
from fuelweb_test.helpers.decorators import upload_manifests
from fuelweb_test.helpers.eb_tables import Ebtables
from fuelweb_test.helpers.fuel_actions import NailgunActions
from fuelweb_test.helpers.fuel_actions import PostgresActions
from fuelweb_test.helpers import multiple_networks_hacks
from fuelweb_test.models.fuel_web_client import FuelWebClient
from fuelweb_test import settings
from fuelweb_test import logwrap
from fuelweb_test import logger


class EnvironmentModel(object):
    hostname = 'nailgun'
    domain = 'test.domain.local'
    installation_timeout = 1800
    deployment_timeout = 1800
    puppet_timeout = 2000
    nat_interface = ''  # INTERFACES.get('admin')
    admin_net = 'admin'
    admin_net2 = 'admin2'
    multiple_cluster_networks = settings.MULTIPLE_NETWORKS
    __wrapped__ = None

    def __init__(self, os_image=None):
        self._virtual_environment = None
        self._keys = None
        self.fuel_web = FuelWebClient(self.get_admin_node_ip(), self)

    @property
    def nailgun_actions(self):
        return NailgunActions(self.d_env.get_admin_remote())

    @property
    def postgres_actions(self):
        return PostgresActions(self.d_env.get_admin_remote())

    @property
    def admin_node_ip(self):
        return self.fuel_web.admin_node_ip

    @logwrap
    def add_syslog_server(self, cluster_id, port=5514):
        self.fuel_web.add_syslog_server(
            cluster_id, self.d_env.router(), port)

    def bootstrap_nodes(self, devops_nodes, timeout=600, skip_timesync=False):
        """Lists registered nailgun nodes
        Start vms and wait until they are registered on nailgun.
        :rtype : List of registered nailgun nodes
        """
        # self.dhcrelay_check()

        for node in devops_nodes:
            logger.info("Bootstrapping node: {}".format(node.name))
            node.start()
            # TODO(aglarendil): LP#1317213 temporary sleep
            # remove after better fix is applied
            time.sleep(2)
        wait(lambda: all(self.nailgun_nodes(devops_nodes)), 15, timeout)

        if not skip_timesync:
            self.sync_time()
        return self.nailgun_nodes(devops_nodes)

    def sync_time(self, nodes_names=None, skip_sync=False):
        if nodes_names is None:
            roles = ['fuel_master', 'fuel_slave']
            nodes_names = [node.name for node in self.d_env.get_nodes()
                           if node.role in roles and
                           node.driver.node_active(node)]
        logger.info("Please wait while time on nodes: {0} "
                    "will be synchronized"
                    .format(', '.join(sorted(nodes_names))))
        new_time = sync_time(self.d_env, nodes_names, skip_sync)
        for name in sorted(new_time):
                logger.info("New time on '{0}' = {1}".format(name,
                                                             new_time[name]))

    @logwrap
    def get_admin_node_ip(self):
        return str(
            self.d_env.nodes(
            ).admin.get_ip_address_by_network_name(
                self.d_env.admin_net))

    @logwrap
    def get_ebtables(self, cluster_id, devops_nodes):
        return Ebtables(self.get_target_devs(devops_nodes),
                        self.fuel_web.client.get_cluster_vlans(cluster_id))

    def get_keys(self, node, custom=None):
        params = {
            'ip': node.get_ip_address_by_network_name(
                self.d_env.admin_net),
            'mask': self.d_env.get_network(
                name=self.d_env.admin_net).ip.netmask,
            'gw': self.d_env.router(),
            'hostname': '.'.join((self.d_env.hostname,
                                  self.d_env.domain)),
            'nat_interface': self.d_env.nat_interface,
            'dns1': settings.DNS,
            'showmenu': 'yes' if custom else 'no'

        }
        keys = (
            "<Wait>\n"
            "<Esc><Enter>\n"
            "<Wait>\n"
            "vmlinuz initrd=initrd.img ks=cdrom:/ks.cfg\n"
            " ip=%(ip)s\n"
            " netmask=%(mask)s\n"
            " gw=%(gw)s\n"
            " dns1=%(dns1)s\n"
            " hostname=%(hostname)s\n"
            " dhcp_interface=%(nat_interface)s\n"
            " showmenu=%(showmenu)s\n"
            " <Enter>\n"
        ) % params
        return keys

    @logwrap
    def get_ssh_to_remote_by_name(self, node_name):
        return self.d_env.get_ssh_to_remote(
            self.fuel_web.get_nailgun_node_by_devops_node(
                self.d_env.get_node(name=node_name))['ip']
        )

    def get_target_devs(self, devops_nodes):
        return [
            interface.target_dev for interface in [
                val for var in map(lambda node: node.interfaces, devops_nodes)
                for val in var]]

    def get_virtual_environment(self):
        if self._virtual_environment is None:
            try:
                return Environment.get(name=settings.ENV_NAME)
            except Exception:
                self._virtual_environment = Environment.describe_environment()
                self._virtual_environment.define()
        return self._virtual_environment

    def _get_network(self, net_name):
        return str(
            IPNetwork(
                self.d_env.get_network(name=net_name).
                ip_network))

    def get_net_mask(self, net_name):
        return str(
            IPNetwork(
                self.d_env.get_network(
                    name=net_name).ip_network).netmask)

    def make_snapshot(self, snapshot_name, description="", is_make=False):
        if settings.MAKE_SNAPSHOT or is_make:
            self.d_env.suspend(verbose=False)
            time.sleep(10)

            self.d_env.snapshot(snapshot_name, force=True)
            revert_info(snapshot_name, description)
            self.d_env.resume()
            try:
                self.d_env.nodes().admin.await(
                    self.d_env.admin_net, timeout=60)
            except Exception:
                logger.error('Admin node is unavailable via SSH after '
                             'environment resume ')
                raise

    def nailgun_nodes(self, devops_nodes):
        return map(
            lambda node: self.fuel_web.get_nailgun_node_by_devops_node(node),
            devops_nodes
        )

    def revert_snapshot(self, name):
        if self.d_env.has_snapshot(name):
            logger.info('We have snapshot with such name %s' % name)

            self.d_env.revert(name)
            logger.info('Starting snapshot reverting ....')

            self.d_env.resume()
            logger.info('Starting snapshot resuming ...')

            admin = self.d_env.nodes().admin

            try:
                admin.await(
                    self.d_env.admin_net, timeout=10 * 60,
                    by_port=8000)
            except Exception as e:
                logger.warning("From first time admin isn't reverted: "
                               "{0}".format(e))
                admin.destroy()
                logger.info('Admin node was destroyed. Wait 10 sec.')
                time.sleep(10)
                self.d_env.start(
                    self.d_env.nodes().admins)
                logger.info('Admin node started second time.')
                self.d_env.nodes().admin.await(
                    self.d_env.admin_net, timeout=10 * 60,
                    by_port=8000)

            self.set_admin_ssh_password()
            try:
                _wait(self.fuel_web.client.get_releases,
                      expected=EnvironmentError, timeout=300)
            except exceptions.Unauthorized:
                self.set_admin_keystone_password()
                self.fuel_web.get_nailgun_version()

            self.sync_time()
            return True
        return False

    def set_admin_ssh_password(self):
        try:
            remote = self.d_env.get_admin_remote(
                login=settings.SSH_CREDENTIALS['login'],
                password=settings.SSH_CREDENTIALS['password'])
            self.execute_remote_cmd(remote, 'date')
            logger.debug('Accessing admin node using SSH: SUCCESS')
        except Exception:
            logger.debug('Accessing admin node using SSH credentials:'
                         ' FAIL, trying to change password from default')
            remote = self.d_env.get_admin_remote(
                login='root', password='r00tme')
            self.execute_remote_cmd(
                remote, 'echo -e "{1}\\n{1}" | passwd {0}'
                .format(settings.SSH_CREDENTIALS['login'],
                        settings.SSH_CREDENTIALS['password']))
            logger.debug("Admin node password has changed.")
        logger.info("Admin node login name: '{0}' , password: '{1}'".
                    format(settings.SSH_CREDENTIALS['login'],
                           settings.SSH_CREDENTIALS['password']))

    def set_admin_keystone_password(self):
        remote = self.d_env.get_admin_remote()
        try:
            self.fuel_web.client.get_releases()
        except exceptions.Unauthorized:
            self.execute_remote_cmd(
                remote, 'fuel user --newpass {0} --change-password'
                .format(settings.KEYSTONE_CREDS['password']))
            logger.info(
                'New Fuel UI (keystone) username: "{0}", password: "{1}"'
                .format(settings.KEYSTONE_CREDS['username'],
                        settings.KEYSTONE_CREDS['password']))

    @property
    def d_env(self):
        return self.get_virtual_environment()

    def setup_environment(self, custom=False):
        # start admin node
        admin = self.d_env.nodes().admin
        admin.disk_devices.get(device='cdrom').volume.upload(settings.ISO_PATH)
        self.d_env.start(self.d_env.nodes().admins)
        logger.info("Waiting for admin node to start up")
        wait(lambda: admin.driver.node_active(admin), 60)
        logger.info("Proceed with installation")
        # update network parameters at boot screen
        admin.send_keys(self.get_keys(admin, custom=custom))
        if custom:
            self.setup_customisation()
        # wait while installation complete
        admin.await(self.d_env.admin_net, timeout=10 * 60)
        self.set_admin_ssh_password()
        self.wait_bootstrap()
        time.sleep(10)
        self.set_admin_keystone_password()
        self.sync_time(['admin'])
        if settings.MULTIPLE_NETWORKS:
            self.describe_second_admin_interface()
            multiple_networks_hacks.configure_second_admin_cobbler(self)
            multiple_networks_hacks.configure_second_dhcrelay(self)
        self.nailgun_actions.set_collector_address(
            settings.FUEL_STATS_HOST,
            settings.FUEL_STATS_PORT,
            settings.FUEL_STATS_SSL)
        # Restart statsenderd in order to apply new settings(Collector address)
        self.nailgun_actions.force_fuel_stats_sending()
        if settings.FUEL_STATS_ENABLED:
            self.fuel_web.client.send_fuel_stats(enabled=True)
            logger.info('Enabled sending of statistics to {0}:{1}'.format(
                settings.FUEL_STATS_HOST, settings.FUEL_STATS_PORT
            ))

    @upload_manifests
    def wait_for_provisioning(self):
        _wait(lambda: _tcp_ping(
            self.d_env.nodes(
            ).admin.get_ip_address_by_network_name
            (self.d_env.admin_net), 22), timeout=5 * 60)

    def setup_customisation(self):
        self.wait_for_provisioning()
        try:
            remote = self.d_env.get_admin_remote()
            pid = remote.execute("pgrep 'fuelmenu'")['stdout'][0]
            pid.rstrip('\n')
            remote.execute("kill -sigusr1 {0}".format(pid))
        except Exception:
            logger.error("Could not kill pid of fuelmenu")
            raise

    @retry(count=10, delay=60)
    @logwrap
    def sync_node_time(self, remote):
        self.execute_remote_cmd(remote, 'hwclock -s')
        self.execute_remote_cmd(remote, 'NTPD=$(find /etc/init.d/ -regex \''
                                        '/etc/init.d/\(ntp.?\|ntp-dev\)\');'
                                        '$NTPD stop && ntpd -dqg && $NTPD '
                                        'start')
        self.execute_remote_cmd(remote, 'hwclock -w')
        remote_date = remote.execute('date')['stdout']
        logger.info("Node time: %s" % remote_date)

    def verify_network_configuration(self, node_name):
        node = self.fuel_web.get_nailgun_node_by_name(node_name)
        checkers.verify_network_configuration(
            node=node,
            remote=self.d_env.get_ssh_to_remote(node['ip'])
        )

    def wait_bootstrap(self):
        logger.info("Waiting while bootstrapping is in progress")
        log_path = "/var/log/puppet/bootstrap_admin_node.log"
        logger.info("Puppet timeout set in {0}".format(
            float(settings.PUPPET_TIMEOUT)))
        wait(
            lambda: not
            self.d_env.get_admin_remote().execute(
                "grep 'Fuel node deployment' '%s'" % log_path
            )['exit_code'],
            timeout=(float(settings.PUPPET_TIMEOUT))
        )
        result = self.d_env.get_admin_remote().execute(
            "grep 'Fuel node deployment "
            "complete' '%s'" % log_path)['exit_code']
        if result != 0:
            raise Exception('Fuel node deployment failed.')

    def dhcrelay_check(self):
        admin_remote = self.d_env.get_admin_remote()
        out = admin_remote.execute("dhcpcheck discover "
                                   "--ifaces eth0 "
                                   "--repeat 3 "
                                   "--timeout 10")['stdout']

        assert_true(self.get_admin_node_ip() in "".join(out),
                    "dhcpcheck doesn't discover master ip")

    def run_nailgun_agent(self, remote):
        agent = remote.execute('/opt/nailgun/bin/agent')['exit_code']
        logger.info("Nailgun agent run with exit_code: %s" % agent)

    def get_fuel_settings(self, remote=None):
        if not remote:
            remote = self.d_env.get_admin_remote()
        cmd = 'cat {cfg_file}'.format(cfg_file=settings.FUEL_SETTINGS_YAML)
        result = remote.execute(cmd)
        if result['exit_code'] == 0:
            fuel_settings = yaml.load(''.join(result['stdout']))
        else:
            raise Exception('Can\'t output {cfg_file} file: {error}'.
                            format(cfg_file=settings.FUEL_SETTINGS_YAML,
                                   error=result['stderr']))
        return fuel_settings

    def admin_install_pkg(self, pkg_name):
        """Install a package <pkg_name> on the admin node"""
        admin_remote = self.d_env.get_admin_remote()
        remote_status = admin_remote.execute("rpm -q {0}'".format(pkg_name))
        if remote_status['exit_code'] == 0:
            logger.info("Package '{0}' already installed.".format(pkg_name))
        else:
            logger.info("Installing package '{0}' ...".format(pkg_name))
            remote_status = admin_remote.execute("yum -y install {0}"
                                                 .format(pkg_name))
            logger.info("Installation of the package '{0}' has been"
                        " completed with exit code {1}"
                        .format(pkg_name, remote_status['exit_code']))
        return remote_status['exit_code']

    def admin_run_service(self, service_name):
        """Start a service <service_name> on the admin node"""
        admin_remote = self.d_env.get_admin_remote()
        admin_remote.execute("service {0} start".format(service_name))
        remote_status = admin_remote.execute("service {0} status"
                                             .format(service_name))
        if any('running...' in status for status in remote_status['stdout']):
            logger.info("Service '{0}' is running".format(service_name))
        else:
            logger.info("Service '{0}' failed to start"
                        " with exit code {1} :\n{2}"
                        .format(service_name,
                                remote_status['exit_code'],
                                remote_status['stdout']))

    # Modifies a resolv.conf on the Fuel master node and returns
    # its original content.
    # * adds 'nameservers' at start of resolv.conf if merge=True
    # * replaces resolv.conf with 'nameservers' if merge=False
    def modify_resolv_conf(self, nameservers=[], merge=True):
        remote = self.d_env.get_admin_remote()
        resolv_conf = remote.execute('cat /etc/resolv.conf')
        assert_equal(0, resolv_conf['exit_code'], 'Executing "{0}" on the '
                     'admin node has failed with: {1}'
                     .format('cat /etc/resolv.conf', resolv_conf['stderr']))
        if merge:
            nameservers.extend(resolv_conf['stdout'])

        resolv_keys = ['search', 'domain', 'nameserver']
        resolv_new = "".join('{0}\n'.format(ns) for ns in nameservers
                             if any(x in ns for x in resolv_keys))
        logger.debug('echo "{0}" > /etc/resolv.conf'.format(resolv_new))
        echo_cmd = 'echo "{0}" > /etc/resolv.conf'.format(resolv_new)
        echo_result = remote.execute(echo_cmd)
        assert_equal(0, echo_result['exit_code'], 'Executing "{0}" on the '
                     'admin node has failed with: {1}'
                     .format(echo_cmd, echo_result['stderr']))
        return resolv_conf['stdout']

    @logwrap
    def execute_remote_cmd(self, remote, cmd, exit_code=0):
        result = remote.execute(cmd)
        assert_equal(result['exit_code'], exit_code,
                     'Failed to execute "{0}" on remote host: {1}'.
                     format(cmd, result))
        return result['stdout']

    @logwrap
    def describe_second_admin_interface(self):
        remote = self.d_env.get_admin_remote()
        admin_net2_object = self.d_env.get_network(name=self.d_env.admin_net2)
        second_admin_network = admin_net2_object.ip.network
        second_admin_netmask = admin_net2_object.ip.netmask
        second_admin_if = settings.INTERFACES.get(self.d_env.admin_net2)
        second_admin_ip = str(self.d_env.nodes(
        ).admin.get_ip_address_by_network_name(self.d_env.admin_net2))
        logger.info(('Parameters for second admin interface configuration: '
                     'Network - {0}, Netmask - {1}, Interface - {2}, '
                     'IP Address - {3}').format(second_admin_network,
                                                second_admin_netmask,
                                                second_admin_if,
                                                second_admin_ip))
        add_second_admin_ip = ('DEVICE={0}\\n'
                               'ONBOOT=yes\\n'
                               'NM_CONTROLLED=no\\n'
                               'USERCTL=no\\n'
                               'PEERDNS=no\\n'
                               'BOOTPROTO=static\\n'
                               'IPADDR={1}\\n'
                               'NETMASK={2}\\n').format(second_admin_if,
                                                        second_admin_ip,
                                                        second_admin_netmask)
        cmd = ('echo -e "{0}" > /etc/sysconfig/network-scripts/ifcfg-{1};'
               'ifup {1}; ip -o -4 a s {1} | grep -w {2}').format(
            add_second_admin_ip, second_admin_if, second_admin_ip)
        logger.debug('Trying to assign {0} IP to the {1} on master node...'.
                     format(second_admin_ip, second_admin_if))
        result = remote.execute(cmd)
        assert_equal(result['exit_code'], 0, ('Failed to assign second admin '
                     'IP address on master node: {0}').format(result))
        logger.debug('Done: {0}'.format(result['stdout']))
        multiple_networks_hacks.configure_second_admin_firewall(
            self,
            second_admin_network,
            second_admin_netmask)

    @logwrap
    def get_masternode_uuid(self):
        return self.postgres_actions.run_query(
            db='nailgun',
            query="select master_node_uid from master_node_settings limit 1;")
