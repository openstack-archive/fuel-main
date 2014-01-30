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

import json
import logging
import paramiko
import time
import random

from fuelweb_test.helpers import common


logger = logging.getLogger(__name__)


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

    def create_server(self, neutron=False):
        name = "test-serv" + str(random.randint(1, 0x7fffffff))
        security_groups = {}
        image_id = self._get_cirros_image().id
        security_groups[self.keystone.tenant_id] =\
            self.create_sec_group_for_ssh()
        security_groups = [security_groups[
                           self.keystone.tenant_id].name]

        if neutron:
            network = [net.id for net in self.nova.networks.list()
                       if net.label == 'net04']

            kwargs = {'nics': [{'net-id': network[0]}],
                      'security_groups': security_groups}
        else:
            kwargs = {'security_groups': security_groups}

        srv = self.nova.servers.create(name=name,
                                       image=image_id,
                                       flavor=1,
                                       **kwargs)
        time.sleep(100)
        return self.nova.servers.get(srv.id)

    def delete_srv(self, srv):
        serv = ""
        self.nova.servers.delete(srv)
        try:
            serv = srv.get()
        except Exception:
            logger.info("Server was successfully deleted")
            return True

        if serv in self.nova.servers.list():
            logger.info("Server was not deleted for some reason")
            raise Exception()

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
        time.sleep(20)
        if self.get_srv_host_name(server) == curr_host:
            logger.info("Server did not migrate")
            raise Exception()
        server = self.nova.servers.get(server.id)
        return server

    def create_volume(self, size=1):
        volume = self.cinder.volumes.create(size)
        time.sleep(100)
        logger.info("Created volume")
        return self.cinder.volumes.get(volume.id)

    def check_srv_state_after_migration(self, server):
        return server.status == "ACTIVE"

    def get_hosts_for_migr(self, srv_host_name):
        # Determine which host is available for live migration
        host_list = filter(lambda host: host.host_name != srv_host_name,
                           self.nova.hosts.list())
        return filter(lambda host: host._info['service'] == 'compute',
                      host_list)

    def create_file_on_vm(self, file_name, controller_ip, vm_ip):
        logger.info("Creating file on VM")
        self.execute_through_host(
            controller_ip, vm_ip, "touch %s" % file_name)
        logger.info("Retrieving file md5sum")
        md5sum = self.execute_through_host(
            controller_ip, vm_ip, "md5sum %s" % file_name)
        return md5sum

    def check_file_exists(self, file_name, md5sum, controller_ip, vm_ip):
        logger.info("Get file md5sum and compare it with previous one")
        out = self.execute_through_host(
            controller_ip, vm_ip, "md5sum %s" % file_name)
        if md5sum not in out:
            logger.info("File md5sum has changed")
            raise Exception()

    def execute_through_host(self, ssh, vm_host, cmd):
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
            transport.auth_password('cirros', 'cubswin:)')

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
