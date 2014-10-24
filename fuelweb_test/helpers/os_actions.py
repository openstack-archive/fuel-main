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

import paramiko
from proboscis import asserts
import random
import time

from devops.error import TimeoutError
from devops.helpers import helpers
from fuelweb_test.helpers import common
from fuelweb_test import logger


class OpenStackActions(common.Common):
    def __init__(self, controller_ip, user='admin',
                 passwd='admin', tenant='admin'):
        super(OpenStackActions, self).__init__(controller_ip,
                                               user, passwd,
                                               tenant)

    def _get_cirros_image(self):
        for image in self.glance.images.list():
            if image.name.startswith("TestVM"):
                return image

    def get_hypervisors(self):
        hypervisors = self.nova.hypervisors.list()
        if hypervisors:
            return hypervisors

    def get_hypervisor_vms_count(self, hypervisor):
        hypervisor = self.nova.hypervisors.get(hypervisor.id)
        return getattr(hypervisor, "running_vms")

    def get_hypervisor_hostanme(self, hypervisor):
        hypervisor = self.nova.hypervisors.get(hypervisor.id)
        return getattr(hypervisor, "hypervisor_hostname")

    def get_srv_hypervisor_name(self, srv):
        srv = self.nova.servers.get(srv.id)
        return getattr(srv, "OS-EXT-SRV-ATTR:hypervisor_hostname")

    def get_servers(self):
        servers = self.nova.servers.list()
        if servers:
            return servers

    def create_server_for_migration(self, neutron=False, scenario='',
                                    timeout=100, file=None):
        name = "test-serv" + str(random.randint(1, 0x7fffffff))
        security_group = {}
        try:
            if scenario:
                with open(scenario, "r+") as f:
                    scenario = f.read()
        except Exception as exc:
            logger.info("Error opening file: %s" % exc)
            raise Exception()
        image_id = self._get_cirros_image().id
        security_group[self.keystone.tenant_id] =\
            self.create_sec_group_for_ssh()
        security_group = [security_group[
            self.keystone.tenant_id].name]

        if neutron:
            network = [net.id for net in self.nova.networks.list()
                       if net.label == 'net04']

            kwargs = {'nics': [{'net-id': network[0]}],
                      'security_groups': security_group}
        else:
            kwargs = {'security_groups': security_group}

        srv = self.nova.servers.create(name=name,
                                       image=image_id,
                                       flavor=1,
                                       userdata=scenario,
                                       files=file,
                                       **kwargs)
        try:
            helpers.wait(
                lambda: self.get_instance_detail(srv).status == "ACTIVE",
                timeout=timeout)
            return self.get_instance_detail(srv.id)
        except TimeoutError:
            logger.debug("Create server for migration failed by timeout")
            asserts.assert_equal(
                self.get_instance_detail(srv).status,
                "ACTIVE",
                "Instance do not reach active state, current state"
                " is {0}".format(self.get_instance_detail(srv).status))

    def verify_srv_deleted(self, srv):
        try:
            if self.get_instance_detail(srv.id):
                logger.info("Try getting server another time.")
                time.sleep(30)
                if self.get_instance_detail(srv.id) in \
                   self.nova.servers.list():
                    return False
        except Exception:
            logger.info("Server was successfully deleted")
            return True

    def assign_floating_ip(self, srv):
        fl_ips_pool = self.nova.floating_ip_pools.list()
        if fl_ips_pool:
            floating_ip = self.nova.floating_ips.create(
                pool=fl_ips_pool[0].name)
            self.nova.servers.add_floating_ip(srv, floating_ip)
            return floating_ip

    def create_sec_group_for_ssh(self):
        name = "test-sg" + str(random.randint(1, 0x7fffffff))
        secgroup = self.nova.security_groups.create(
            name, "descr")

        rulesets = [
            {
                # ssh
                'ip_protocol': 'tcp',
                'from_port': 22,
                'to_port': 22,
                'cidr': '0.0.0.0/0',
            },
            {
                # ping
                'ip_protocol': 'icmp',
                'from_port': -1,
                'to_port': -1,
                'cidr': '0.0.0.0/0',
            }
        ]

        for ruleset in rulesets:
            self.nova.security_group_rules.create(
                secgroup.id, **ruleset)
        return secgroup

    def get_srv_host_name(self, srv):
        # Get host name server is currently on
        srv = self.nova.servers.get(srv.id)
        return getattr(srv, "OS-EXT-SRV-ATTR:host")

    def migrate_server(self, server, host, timeout):
        curr_host = self.get_srv_host_name(server)
        logger.debug("Current compute host is {0}".format(curr_host))
        logger.debug("Start live migration of instance")
        server.live_migrate(host._info['host_name'])
        try:
            helpers.wait(
                lambda: self.get_instance_detail(server).status == "ACTIVE",
                timeout=timeout)
        except TimeoutError:
            logger.debug("Instance do not became active after migration")
            asserts.assert_true(
                self.get_instance_detail(server).status == "ACTIVE",
                "Instance do not become Active after live migration, "
                "current status is {0}".format(
                    self.get_instance_detail(server).status))

        asserts.assert_true(
            self.get_srv_host_name(
                self.get_instance_detail(server)) != curr_host,
            "Server did not migrate")
        server = self.get_instance_detail(server.id)
        return server

    def create_volume(self, size=1):
        volume = self.cinder.volumes.create(size)
        helpers.wait(
            lambda: self.cinder.volumes.get(volume.id).status == "available",
            timeout=100)
        logger.info("Created volume")
        return self.cinder.volumes.get(volume.id)

    def attach_volume(self, volume, server, mount='/dev/vdb'):
        self.cinder.volumes.attach(volume, server.id, mount)
        return self.cinder.volumes.get(volume.id)

    def get_hosts_for_migr(self, srv_host_name):
        # Determine which host is available for live migration
        host_list = filter(lambda host: host.host_name != srv_host_name,
                           self.nova.hosts.list())
        return filter(lambda host: host._info['service'] == 'compute',
                      host_list)

    def get_md5sum(self, file_path, controller_ssh, vm_ip, creds=()):
        logger.info("Get file md5sum and compare it with previous one")
        out = self.execute_through_host(
            controller_ssh, vm_ip, "md5sum %s" % file_path, creds)
        return out

    def execute_through_host(self, ssh, vm_host, cmd, creds=()):
        try:
            logger.info("Making intermediate transport")
            interm_transp = ssh._ssh.get_transport()
            logger.info("Opening channel to VM")
            interm_chan = interm_transp.open_channel('direct-tcpip',
                                                     (vm_host, 22),
                                                     (ssh.host, 0))
            logger.info("Opening paramiko transport")
            transport = paramiko.Transport(interm_chan)
            logger.info("Starting client")
            transport.start_client()
            logger.info("Passing authentication to VM")
            if not creds:
                creds = ('cirros', 'cubswin:)')
            transport.auth_password(creds[0], creds[1])

            logger.info("Opening session")
            channel = transport.open_session()
            logger.info("Executing command")
            channel.exec_command(cmd)
            logger.info("Getting exit status")
            output = channel.recv(1024)
            logger.info("Sending shutdown write signal")
            channel.shutdown_write()
            return output
        except Exception as exc:
            logger.error("An exception occurred: %s" % exc)
            return ''

    def get_tenant(self, tenant_name):
        tenant_list = self.keystone.tenants.list()
        for ten in tenant_list:
            if ten.name == tenant_name:
                return ten
        return None

    def get_user(self, username):
        user_list = self.keystone.users.list()
        for user in user_list:
            if user.name == username:
                return user
        return None

    def create_tenant(self, tenant_name):
        tenant = self.get_tenant(tenant_name)
        if tenant:
            return tenant
        return self.keystone.tenants.create(enabled=True,
                                            tenant_name=tenant_name)

    def create_user(self, username, passw, tenant):
        user = self.get_user(username)
        if user:
            return user
        return self.keystone.users.create(
            name=username, password=passw, tenant_id=tenant.id)

    def create_user_and_tenant(self, tenant_name, username, password):
        tenant = self.create_tenant(tenant_name)
        return self.create_user(username, password, tenant)

    def get_network(self, network_name):
        net_list = self.neutron.list_networks()
        for net in net_list['networks']:
            if net['name'] == network_name:
                return net
        return None

    def get_router(self, network):
        router_list = self.neutron.list_routers()
        for router in router_list['routers']:
            network_id = router['external_gateway_info'].get('network_id')
            if network_id == network['id']:
                return router
        return None

    def get_image_list(self):
        return self.glance.images.list()

    def get_image(self, image_name):
        image_list = self.get_image_list()
        for img in image_list:
            if img.name == image_name:
                return img
        return None

    def get_image_data(self, image_name):
        return self.glance.images.data(image_name)

    def get_nova_service_list(self):
        return self.nova.services.list()

    def get_nova_network_list(self):
        return self.nova.networks.list()
