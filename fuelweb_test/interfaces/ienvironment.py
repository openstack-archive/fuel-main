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

from zope.interface import Interface
from zope.interface import Attribute


class IEnvironment(Interface):
    """Interface for Environment"""

    hostname = Attribute("""Fuel admin node hostname""")

    domain = Attribute("""Environment domain""")

    installation_timeout = Attribute("""Installation timeout""")

    deployment_timeout = Attribute("""Deployment timeout""")

    puppet_timeout = Attribute("""Puppet timeout""")

    nat_interface = Attribute("""""")

    admin_net = Attribute("""Admin ip network""")

    fuel_web = Attribute("""FuelWebClient instance""")

    admin_node_ip = Attribute("""Fule master node ip address""")

    node_roles = Attribute("""Node roles""")

    env_name = Attribute("""Environment name""")

    def __init__(os_image=None):
        """Constructor"""

    def _get_or_create():
        """"""

    def router(router_name=None):
        """"""

    def add_empty_volume(node, name, capacity,
                         device='disk', bus='virtio', format='qcow2'):
        """Add empty volume to env"""

    def add_node(memmory, name, vcpu, boot=None):
        """Add node to env"""

    def add_syslog_server(cluster_id, port=5514):
        """Add syslog server to env"""

    def bootstrap_nodes(devops_nodes, timeout=600):
        """Bootstrap nodes in env"""

    def create_interfaces(network, node, model):
        """Create network interface"""

    def describe_environment():
        """Describe environment"""

    def create_networks(name, environment):
        """Create network for environment"""

    def devops_nodes_by_names(devops_node_names):
        """Return nodes name from devops"""

    def describe_admin_node(name, networks):
        """Describe admin node"""

    def describe_empty_node(name, networks):
        """Describe slave empty node"""

    def get_admin_remote():
        """Get remote console to admin node"""

    def get_admin_node_ip():
        """Fetch admin node ip address"""

    def get_ebtables(cluster_id, devops_nodes):
        """Fetch Ebtables"""

    def get_host_node_ip():
        """Return self ip"""

    def get_keys(node, custom=None):
        """Get boot kenrel string"""

    def get_private_keys(force=False):
        """Get host privete key"""

    def get_ssh_to_remote(ip):
        """Get remote console to host by ip"""

    def get_ssh_to_remote_by_name(node_name):
        """Get remote console to host by node name"""

    def get_target_devs(devops_nodes):
        """Get host interfaces"""

    def get_virtual_environment():
        """Get virtual environment"""

    def get_network(net_name):
        """Get IPNetwork to net_name"""

    def get_net_mask(net_name):
        """Get network mask to net_name"""

    def make_snapshot(snapshot_name, description="", is_make=False):
        """Make named environment snapshot"""

    def nailgun_nodes(devops_nodes):
        """Get nailgun node"""

    def nodes():
        """Get nodes in environment"""

    def revert_snapshot(name):
        """Revert environment to state in snapshot"""

    def setup_environment(custom=False):
        """Setup environment"""

    def wait_for_provisioning():
        """Wait for provisioning"""

    def setup_customisation():
        """"""

    def sync_node_time(remote):
        """Sync time on node"""

    def sync_time_admin_node():
        """Sync time on admin node"""

    def verify_node_service_list(node_name, smiles_count):
        """Verify node service list"""

    def verify_network_configuration(node_name):
        """Verify network configuration on node"""

    def wait_bootstrap():
        """Waiting bootstrap node"""

    def dhcrelay_check():
        """DHCP replay check on admin node"""

    def run_nailgun_agent(remote):
        """Run nailgun agent on remote"""

    def get_fuel_settings(remote=None):
        """Get Fuel settings"""

    def admin_install_pkg(pkg_name):
        """Install package to admin node"""

    def admin_run_service(service_name):
        """Run service on admine node"""

    def modify_resolv_conf(nameservers=[], merge=True):
        """Modify resolv.conf on admin node"""

    def execute_remote_cmd(remote, cmd, exit_code=0):
        """Remote command on remote host"""
