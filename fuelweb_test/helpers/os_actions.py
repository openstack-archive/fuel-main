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
import proboscis
import random
import time

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

    def create_server_for_migration(self, neutron=False, scenario=''):
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
                                       **kwargs)
        helpers.wait(
            lambda: self.get_instance_detail(srv).status == "ACTIVE",
            timeout=100)
        return self.get_instance_detail(srv.id)

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

    def migrate_server(self, server, host):
        curr_host = self.get_srv_host_name(server)
        server.live_migrate(host._info['host_name'])
        helpers.wait(
            lambda: self.get_instance_detail(server).status == "ACTIVE",
            timeout=60)
        proboscis.asserts.assert_true(
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
            logger.info("An exception occured: %s" % exc)
