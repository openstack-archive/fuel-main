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

import os

from devops.helpers.helpers import tcp_ping
from devops.helpers.helpers import wait
from fuelweb_test.models.environment import EnvironmentModel
from fuelweb_test import settings


class PuppetEnvironment(EnvironmentModel):
    """Create environment for puppet modules testing."""

    def __init__(self, os_image=None):
        """Constructor for create environment."""
        self.os_image = os_image or settings.OS_IMAGE
        super(PuppetEnvironment, self).__init__(self.os_image)
        self.environment = super(PuppetEnvironment, self).d_env
        self.start_env()

    @property
    def env_name(self):
        return os.environ.get('PPENV_NAME', 'pp-integration')

    def start_env(self):
        self.d_env.start(self.d_env.nodes())

    def execute_cmd(self, command, debug=True):
        """Execute command on node."""
        return self.d_env.get_admin_remote().execute(
            command, verbose=debug)['exit_code']

    def await(self, timeout=1200):
        wait(
            lambda: tcp_ping(self.get_admin_node_ip(), 22), timeout=timeout)


if __name__ == "__main__":
    env = PuppetEnvironment(
        '/var/lib/libvirt/images/ubuntu-12.04.1-server-amd64-p2.qcow2')
    env.await()
    env.make_snapshot(snapshot_name="test1")
    env.execute_cmd('apt-get install mc')
