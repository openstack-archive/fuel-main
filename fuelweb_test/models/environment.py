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
from devops.models import Environment
from ipaddr import IPNetwork
from keystoneclient import exceptions
from paramiko import Agent
from paramiko import RSAKey
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
    def __init__(self):
        self._virtual_environment = None
        self._keys = None
        self.fuel_web = FuelWebClient(self.get_admin_node_ip(), self)

    @property
    def nailgun_actions(self):
        return NailgunActions(self.get_admin_remote())

    @property
    def postgres_actions(self):
        return PostgresActions(self.get_admin_remote())

    @property
    def admin_node_ip(self):
        return self.fuel_web.admin_node_ip

    @logwrap
    def add_syslog_server(self, cluster_id, port=5514):
        self.fuel_web.add_syslog_server(
            cluster_id, self.get_virtual_environment().router(), port)

    def bootstrap_nodes(self, devops_nodes, timeout=600):
        """Lists registered nailgun nodes
        Start vms and wait until they are registered on nailgun.
        :rtype : List of registered nailgun nodes
        """
        # self.dhcrelay_check()

        for node in devops_nodes:
            node.start()
            # TODO(aglarendil): LP#1317213 temporary sleep
            # remove after better fix is applied
            time.sleep(2)
        wait(lambda: all(self.nailgun_nodes(devops_nodes)), 15, timeout)

        for node in self.nailgun_nodes(devops_nodes):
            self.sync_node_time(self.get_ssh_to_remote(node["ip"]))

        return self.nailgun_nodes(devops_nodes)

    @logwrap
    def get_admin_remote(self, login=settings.SSH_CREDENTIALS['login'],
                         password=settings.SSH_CREDENTIALS['password']):
        """SSH to admin node
        :rtype : SSHClient
        """
        return self.get_virtual_environment().nodes().admin.remote(
            self.get_virtual_environment().admin_net,
            login=login,
            password=password)

    @logwrap
    def get_admin_node_ip(self):
        return str(
            self.get_virtual_environment().nodes(
            ).admin.get_ip_address_by_network_name(
                self.get_virtual_environment().admin_net))

    @logwrap
    def get_ebtables(self, cluster_id, devops_nodes):
        return Ebtables(self.get_target_devs(devops_nodes),
                        self.fuel_web.client.get_cluster_vlans(cluster_id))

    def get_keys(self, node, custom=None, build_images=None):
        params = {
            'ip': node.get_ip_address_by_network_name(
                self.get_virtual_environment().admin_net),
            'mask': self.get_net_mask(self.get_virtual_environment(
            ).admin_net),
            'gw': self.get_virtual_environment().router(),
            'hostname': '.'.join((self.get_virtual_environment().hostname,
                                  self.get_virtual_environment().domain)),
            'nat_interface': self.get_virtual_environment().nat_interface,
            'dns1': settings.DNS,
            'showmenu': 'yes' if custom else 'no',
            'build_images': '1' if build_images else '0'

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
            " build_images=%(build_images)s\n"
            " <Enter>\n"
        ) % params
        return keys

    @logwrap
    def get_private_keys(self, force=False):
        if force or self._keys is None:
            self._keys = []
            for key_string in ['/root/.ssh/id_rsa',
                               '/root/.ssh/bootstrap.rsa']:
                with self.get_admin_remote().open(key_string) as f:
                    self._keys.append(RSAKey.from_private_key(f))
        return self._keys

    @logwrap
    def get_ssh_to_remote(self, ip):
        return SSHClient(ip,
                         username=settings.SSH_CREDENTIALS['login'],
                         password=settings.SSH_CREDENTIALS['password'],
                         private_keys=self.get_private_keys())

    @logwrap
    def get_ssh_to_remote_by_key(self, ip, keyfile):
        try:
            with open(keyfile) as f:
                keys = [RSAKey.from_private_key(f)]
                return SSHClient(ip, private_keys=keys)
        except IOError:
            logger.warning('Loading of SSH key from file failed. Trying to use'
                           ' SSH agent ...')
            keys = Agent().get_keys()
            return SSHClient(ip, private_keys=keys)

    @logwrap
    def get_ssh_to_remote_by_name(self, node_name):
        return self.get_ssh_to_remote(
            self.fuel_web.get_nailgun_node_by_devops_node(
                self.get_virtual_environment().get_node(name=node_name))['ip']
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
                self.get_virtual_environment().get_network(name=net_name).
                ip_network))

    def get_net_mask(self, net_name):
        return str(
            IPNetwork(
                self.get_virtual_environment().get_network(
                    name=net_name).ip_network).netmask)

    def make_snapshot(self, snapshot_name, description="", is_make=False):
        if settings.MAKE_SNAPSHOT or is_make:
            self.get_virtual_environment().suspend(verbose=False)
            time.sleep(10)
            self.get_virtual_environment().snapshot(snapshot_name, force=True)
            revert_info(snapshot_name, description)
            self.get_virtual_environment().resume()
            try:
                self.get_virtual_environment().nodes().admin.await(
                    self.get_virtual_environment().admin_net, timeout=60)
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
        if self.get_virtual_environment().has_snapshot(name):
            logger.info('We have snapshot with such name %s' % name)

            self.get_virtual_environment().revert(name)
            logger.info('Starting snapshot reverting ....')

            self.get_virtual_environment().resume()
            logger.info('Starting snapshot resuming ...')

            admin = self.get_virtual_environment().nodes().admin

            try:
                admin.await(
                    self.get_virtual_environment().admin_net, timeout=10 * 60,
                    by_port=8000)
            except Exception as e:
                logger.warning("From first time admin isn't reverted: "
                               "{0}".format(e))
                admin.destroy()
                logger.info('Admin node was destroyed. Wait 10 sec.')
                time.sleep(10)
                self.get_virtual_environment().start(
                    self.get_virtual_environment().nodes().admins)
                logger.info('Admin node started second time.')
                self.get_virtual_environment().nodes().admin.await(
                    self.get_virtual_environment().admin_net, timeout=10 * 60,
                    by_port=8000)

            self.set_admin_ssh_password()
            try:
                _wait(self.fuel_web.client.get_releases,
                      expected=EnvironmentError, timeout=300)
            except exceptions.Unauthorized:
                self.set_admin_keystone_password()
                self.fuel_web.get_nailgun_version()

            self.sync_time_admin_node()

            for node in self.get_virtual_environment().nodes(
            ).slaves:
                if not node.driver.node_active(node):
                    continue
                try:
                    logger.info("Sync time on revert for node %s" % node.name)
                    self.sync_node_time(
                        self.get_ssh_to_remote_by_name(node.name))
                except Exception as e:
                    logger.warning(
                        'Exception caught while trying to sync time on {0}:'
                        ' {1}'.format(node.name, e))
                self.run_nailgun_agent(
                    self.get_ssh_to_remote_by_name(node.name))
            return True
        return False

    def set_admin_ssh_password(self):
        try:
            remote = self.get_admin_remote(
                login=settings.SSH_CREDENTIALS['login'],
                password=settings.SSH_CREDENTIALS['password'])
            self.execute_remote_cmd(remote, 'date')
            logger.debug('Accessing admin node using SSH: SUCCESS')
        except Exception:
            logger.debug('Accessing admin node using SSH credentials:'
                         ' FAIL, trying to change password from default')
            remote = self.get_admin_remote(login='root', password='r00tme')
            self.execute_remote_cmd(
                remote, 'echo -e "{1}\\n{1}" | passwd {0}'
                .format(settings.SSH_CREDENTIALS['login'],
                        settings.SSH_CREDENTIALS['password']))
            logger.debug("Admin node password has changed.")
        logger.info("Admin node login name: '{0}' , password: '{1}'".
                    format(settings.SSH_CREDENTIALS['login'],
                           settings.SSH_CREDENTIALS['password']))

    def set_admin_keystone_password(self):
        remote = self.get_admin_remote()
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

    def setup_environment(self, custom=settings.CUSTOM_ENV,
                          build_images=settings.BUILD_IMAGES):
        # start admin node
        admin = self.get_virtual_environment().nodes().admin
        admin.disk_devices.get(device='cdrom').volume.upload(settings.ISO_PATH)
        self.get_virtual_environment().start(self.get_virtual_environment(
        ).nodes().admins)
        logger.info("Waiting for admin node to start up")
        wait(lambda: admin.driver.node_active(admin), 60)
        logger.info("Proceed with installation")
        # update network parameters at boot screen
        admin.send_keys(self.get_keys(admin, custom=custom,
                        build_images=build_images))
        if custom:
            self.setup_customisation()
        # wait while installation complete
        admin.await(self.get_virtual_environment().admin_net, timeout=10 * 60)
        self.set_admin_ssh_password()
        self.wait_bootstrap()
        time.sleep(10)
        self.set_admin_keystone_password()
        self.sync_time_admin_node()
        if settings.MULTIPLE_NETWORKS:
            self.describe_second_admin_interface()
            multiple_networks_hacks.configure_second_admin_cobbler(self)
            multiple_networks_hacks.configure_second_dhcrelay(self)
        self.nailgun_actions.set_collector_address(
            settings.FUEL_STATS_HOST,
            settings.FUEL_STATS_PORT,
            settings.FUEL_STATS_SSL)
        if settings.FUEL_STATS_ENABLED:
            self.fuel_web.client.send_fuel_stats(enabled=True)
            logger.info('Enabled sending of statistics to {0}:{1}'.format(
                settings.FUEL_STATS_HOST, settings.FUEL_STATS_PORT
            ))

    @upload_manifests
    def wait_for_provisioning(self):
        _wait(lambda: _tcp_ping(
            self.get_virtual_environment().nodes(
            ).admin.get_ip_address_by_network_name
            (self.get_virtual_environment().admin_net), 22), timeout=5 * 60)

    def setup_customisation(self):
        self.wait_for_provisioning()
        try:
            remote = self.get_admin_remote()
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

    @retry(count=10, delay=60)
    @logwrap
    def sync_time_admin_node(self):
        logger.info("Sync time on revert for admin")
        remote = self.get_admin_remote()
        self.execute_remote_cmd(remote, 'hwclock -s')
        # Sync time using ntpd
        try:
            # If public NTP servers aren't accessible ntpdate will fail and
            # ntpd daemon shouldn't be restarted to avoid 'Server has gone
            # too long without sync' error while syncing time from slaves
            self.execute_remote_cmd(remote, "ntpdate -vu $(awk '/^server/ && "
                                            "$2 !~ /127.*/ {print $2}' "
                                            "/etc/ntp.conf)")
        except AssertionError as e:
            logger.warning('Error occurred while synchronizing time on master'
                           ': {0}'.format(e))
            raise
        else:
            self.execute_remote_cmd(remote, 'service ntpd stop && ntpd -dqg &&'
                                            ' service ntpd start')
            self.execute_remote_cmd(remote, 'hwclock -w')

        remote_date = remote.execute('date')['stdout']
        logger.info("Master node time: {0}".format(remote_date))

    def verify_network_configuration(self, node_name):
        checkers.verify_network_configuration(
            node=self.fuel_web.get_nailgun_node_by_name(node_name),
            remote=self.get_ssh_to_remote_by_name(node_name)
        )

    def wait_bootstrap(self):
        logger.info("Waiting while bootstrapping is in progress")
        log_path = "/var/log/puppet/bootstrap_admin_node.log"
        logger.info("Puppet timeout set in {0}".format(
            float(settings.PUPPET_TIMEOUT)))
        wait(
            lambda: not
            self.get_admin_remote().execute(
                "grep 'Fuel node deployment' '%s'" % log_path
            )['exit_code'],
            timeout=(float(settings.PUPPET_TIMEOUT))
        )
        result = self.get_admin_remote().execute("grep 'Fuel node deployment "
                                                 "complete' '%s'" % log_path
                                                 )['exit_code']
        if result != 0:
            raise Exception('Fuel node deployment failed.')

    def dhcrelay_check(self):
        admin_remote = self.get_admin_remote()
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
            remote = self.get_admin_remote()
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
        admin_remote = self.get_admin_remote()
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
        admin_remote = self.get_admin_remote()
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
        remote = self.get_admin_remote()
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
        remote = self.get_admin_remote()
        second_admin_network = self._get_network(self.get_virtual_environment(
        ).admin_net2).split('/')[0]
        second_admin_netmask = self.get_net_mask(self.get_virtual_environment(
        ).admin_net2)
        second_admin_if = settings.INTERFACES.get(self.get_virtual_environment(
        ).admin_net2)
        second_admin_ip = str(self.get_virtual_environment().nodes(
        ).admin.get_ip_address_by_network_name(self.get_virtual_environment(
        ).admin_net2))
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
