import json
import logging
import paramiko
import time
import random


from fuelweb_test.helpers import common


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

    def create_server(self):
        name  = "test-serv" + str(random.randint(1, 0x7fffffff))

        security_groups = {}
        image_id = self._get_cirros_image().id
        security_groups[self.keystone.tenant_id] =\
            self.create_sec_group_for_ssh()
        security_groups = [security_groups[
                           self.keystone.tenant_id].name]
        kwargs = {'security_groups':
                  security_groups}
        srv = self.nova.servers.create(name,
                                       image_id, 1,
                                       **kwargs)
        time.sleep(30)
        return self.nova.servers.get(srv.id)

    def delete_srv(self, srv):
        self.nova.servers.delete(srv)
        time.sleep(30)
        if srv in self.nova.servers.list():
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
            "testg", "descr")

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
            raise Exception()
        server = self.nova.servers.get(server.id)
        return server

    def create_volume(self, size=1):
        volume = self.cinder.volumes.create(size)
        time.sleep(100)
        return self.cinder.volumes.get(volume.id)

    def check_srv_state_after_migration(self, server, unchanged_params=None,
                                        changed_params=None):
        if unchanged_params:
            unchanged = filter(lambda attr: getattr(server, attr) \
                               !=unchanged_params[attr], unchanged_params)
        if changed_params:
            changed = filter(lambda attr: getattr(server, attr) \
                             == changed_params[attr], changed_params)
        return bool(unchanged and changed)

    def get_hosts_for_migr(self, srv_host_name):
        # Determine which host is available for live migration
        host_list = filter(lambda host: host.host_name != srv_host_name, \
                           self.nova.hosts.list())
        return filter(lambda host: host._info['service'] == 'compute',
                      host_list)
