# vim: ts=4 sw=4 expandtab
from devops import xml, scancodes
import os
import tempfile
import time
import subprocess
import shlex
from collections import deque
from xmlbuilder import XMLBuilder
import ipaddr
import re

import logging

logger = logging.getLogger('devops.libvirt')


def index(p, seq):
    for i in xrange(len(seq)):
        if p(seq[i]):
            return i
    return -1


def find(p, seq):
    for item in seq:
        if p(item):
            return item
    return None


def spec_priority(spec):
    if spec.hypervisor == 'qemu':
        return 0.5
    return 1.0


class DeploymentSpec:
    def __repr__(self):
        return "<DeploymentSpec arch=\"%s\" os_type=\"%s\" hypervisor=\"%s\" emulator=\"%s\">" %\
               (self.arch, self.os_type, self.hypervisor, self.emulator)


class LibvirtException(Exception):
    pass


class LibvirtXMLBuilder:
    def build_network_xml(self, network):
        network_xml = XMLBuilder('network')
        network_xml.name(network.id)
        network_xml.forward(mode='nat')

        if hasattr(network, 'ip_addresses') and not network.ip_addresses is None:
            with network_xml.ip(
                address=str(network.ip_addresses[1]),
                prefix=str(network.ip_addresses.prefixlen)
            ):
                if network.pxe:
                    network_xml.tftp(root=network.tftp_root_dir)
                if network.dhcp_server:
                    with network_xml.dhcp:
                        if hasattr(network, 'dhcp_dynamic_address_start'):
                            start = network.dhcp_dynamic_address_start
                        else:
                            start = network.ip_addresses[2]

                        if hasattr(network, 'dhcp_dynamic_address_end'):
                            end = network.dhcp_dynamic_address_end
                        else:
                            end = network.ip_addresses[
                                network.ip_addresses.numhosts - 2]
                        allowed_addresses = list(network.ip_addresses)[2: network.ip_addresses.numhosts - 2]
                        network_xml.range(start=str(start), end=str(end))
                        for interface in network.interfaces:
                            address = find(
                                lambda ip: ip in allowed_addresses,
                                interface.ip_addresses)
                            if address and interface.mac_address:
                                network_xml.host(
                                    mac=str(interface.mac_address),
                                    ip=str(address), name=interface.node.name)
                        if network.pxe:
                            network_xml.bootp(file="pxelinux.0")

        return str(network_xml)

    def build_node_xml(self, node, spec):
        node_xml = XMLBuilder("domain", type=spec.hypervisor)
        node_xml.name(node.id)
        node_xml.vcpu(str(node.cpu))
        node_xml.memory(str(node.memory * 1024), unit='KiB')

        with node_xml.os:
            node_xml.type(spec.os_type, arch=node.arch)
            for boot_dev in node.boot:
                if boot_dev == 'disk':
                    node_xml.boot(dev="hd")
                else:
                    node_xml.boot(dev=boot_dev)

        ide_disk_names = deque(
            ['hd' + c for c in list('abcdefghijklmnopqrstuvwxyz')])
        serial_disk_names = deque(
            ['sd' + c for c in list('abcdefghijklmnopqrstuvwxyz')])

        def disk_name(bus='ide'):
            if str(bus) == 'ide':
                return ide_disk_names.popleft()
            return serial_disk_names.popleft()
        with node_xml.devices:
            node_xml.emulator(spec.emulator)

            if len(node.disks) > 0:
                node_xml.controller(type="ide")

            for disk in node.disks:
                with node_xml.disk(type="file", device="disk"):
                    node_xml.driver(
                        name="qemu", type=disk.format,
                        cache="unsafe")
                    node_xml.source(file=disk.path)
                    node_xml.target(dev=disk_name(disk.bus), bus=disk.bus)

            if node.cdrom:
                with node_xml.disk(type="file", device="cdrom"):
                    node_xml.driver(name="qemu", type="raw")
                    node_xml.source(file=node.cdrom.isopath)
                    node_xml.target(
                        dev=disk_name(node.cdrom.bus),
                        bus=node.cdrom.bus)

            for interface in node.interfaces:
                with node_xml.interface(type="network"):
                    node_xml.source(network=interface.network.id)

            for interface in node.bridged_interfaces:
                with node_xml.interface(type="bridge"):
                    node_xml.source(bridge=interface.bridge)

            if node.vnc:
                node_xml.graphics(type='vnc', listen='0.0.0.0', autoport='yes')

        return str(node_xml)


class Libvirt:
    def __init__(self, xml_builder=LibvirtXMLBuilder(), virsh_cmd=None):
        if not virsh_cmd: virsh_cmd = [
            'virsh']
        self.xml_builder = xml_builder
        self._virsh_cmd = virsh_cmd
        self._init_capabilities()

    @property
    def virsh_cmd(self):
        return self._virsh_cmd[:]

    def node_exists(self, node_name):
        return self._system(
            self.virsh_cmd + ['dominfo', node_name],
            expected_resultcodes=(0, 1)) == 0

    def disk_exists(self, disk_name, pool='default'):
        return self._system(
            self.virsh_cmd + ["vol-info",disk_name, '--pool', pool],
            expected_resultcodes=(0, 1)) == 0

    def network_exists(self, network_name):
        return self._system(
            self.virsh_cmd + ['net-info', network_name, '2>/dev/null'],
            expected_resultcodes=(0, 1)) == 0

    def create_network(self, network):
        if not hasattr(network, 'id') or network.id is None:
            network.id = self._generate_network_id(network.name)
        elif self.is_network_defined(network):
            self._virsh(['net-undefine', network.id])

        xml_file = tempfile.NamedTemporaryFile(delete=False)
        network_xml = self.xml_builder.build_network_xml(network)
        logger.debug(
            "libvirt: Building network with following XML:\n%s" % network_xml)
        xml_file.write(network_xml)
        xml_file.close()
        self._virsh(['net-define', xml_file.name])
        os.unlink(xml_file.name)


        network_element = self.get_output_as_xml(self.virsh_cmd + ['net-dumpxml',network.id])

        network.bridge_name = network_element.find('bridge/@name')
        network.mac_address = network_element.find('mac/@address')

    def delete_network(self, network):
        if self.is_network_defined(network):
            logger.debug("Network %s is defined. Undefining.")
            self._virsh(['net-undefine', network.id])

    def start_network(self, network):
        if not self.is_network_running(network):
            logger.debug("Network %s is not running. Starting.")
            self._virsh(['net-start', network.id])

    def stop_network(self, network):
        if self.is_network_running(network):
            logger.debug("Network %s is running. Stopping.")
            self._virsh(['net-destroy', network.id])

    def _get_node_xml(self, node):
        return self.get_output_as_xml(
            self.virsh_cmd + ['dumpxml',node.id])

    def _get_volume_xml(self, name, pool='default'):
        return  self.get_output_as_xml(self.virsh_cmd + ['vol-dumpxml', name, '--pool', pool])

    def _get_volume_capacity(self, name, pool='default'):
        xml = self._get_volume_xml(name, pool)
        return xml.find('capacity').text

    def create_node(self, node):
        specs = filter(lambda spec: spec.arch == node.arch, self.specs)
        if not len(specs):
            raise LibvirtException, "Can't create node %s: insufficient capabilities" % node.name

        specs.sort(key=spec_priority)
        spec = specs[-1]

        if not hasattr(node, 'id') or node.id is None:
            node.id = self._generate_node_id(node.name)

        xml_file = tempfile.NamedTemporaryFile(delete=False)
        node_xml = self.xml_builder.build_node_xml(node, spec)
        logger.debug(
            "libvirt: Building node with following XML:\n%s" % node_xml)
        xml_file.write(node_xml)
        xml_file.close()
        self._virsh(['define', xml_file.name])
        os.unlink(xml_file.name)

        domain = self._get_node_xml(node)

        for interface_element in domain.find_all(
            'devices/interface[@type="network"]'
        ):
            network_id = interface_element.find('source/@network')

            interface = find(
                lambda i: i.network.id == network_id,
                node.interfaces)
            if interface is None:
                continue

            interface.mac_address = interface_element.find('mac/@address')

    def delete_node(self, node):
        if self.is_node_defined(node):
            logger.debug("Node %s defined. Undefining." % node.id)
            self._virsh(['undefine', node.id])

    def start_node(self, node):
        if not self.is_node_running(node):
            logger.debug(
                "Node %s is not running at the moment. Starting." % node.id)
            self._virsh(['start', node.id])

        if node.vnc:
            domain = self._get_node_xml(node)

            port_text = domain.find('devices/graphics[@type="vnc"]/@port')
            if port_text:
                node.vnc_port = int(port_text)

    def stop_node(self, node):
        if self.is_node_running(node):
            logger.debug(
                "Node %s is running at the moment. Stopping." % node.id)
            self._virsh(['destroy', node.id])

    def reset_node(self, node):
        self._virsh(['reset', node.id])

    def reboot_node(self, node):
        self._virsh(['reboot', node.id])

    def shutdown_node(self, node):
        self._virsh(['stop', node.id])

    def get_node_snapshots(self, node):
        command = self.virsh_cmd + ['snapshot-list', node.id]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        process.wait()
        if process.returncode:
            logger.error(
                "Command '{0:>s}' returned {1:d}, stderr: {2:>s}".format(
                    command, process.returncode, process.stderr.read()))
        else:
            logger.debug(
                "Command '{0:>s}' returned {1:d}".format(command,
                    process.returncode))

        snapshot_ids = []
        for line in process.stdout.readlines()[2:]:
            if line.strip() == '':
                continue
            snapshot_ids.append(line.split()[0])

        return snapshot_ids

    def create_snapshot(self, node, name=None, description=None):
        if not name:
            name = str(int(time.time() * 100))

        xml_file = tempfile.NamedTemporaryFile(delete=False)
        snapshot_xml = XMLBuilder('domainsnapshot')
        snapshot_xml.name(name)
        if description:
            snapshot_xml.description(description)
        logger.debug(
            "Building snapshot with following XML:\n%s" % str(snapshot_xml))
        xml_file.write(str(snapshot_xml))
        xml_file.close()
        self._virsh(['snapshot-create', node.id, xml_file.name])
        os.unlink(xml_file.name)

        return name

    def revert_snapshot(self, node, snapshot_name=None):
        if not snapshot_name:
            snapshot_name = '--current'
        self._virsh(['snapshot-revert', node.id, snapshot_name])

    def delete_snapshot(self, node, snapshot_name=None):
        if not snapshot_name:
            snapshot_name = '--current'
        self._virsh(['snapshot-delete', node.id, snapshot_name])

    def send_keys_to_node(self, node, keys):
        keys = scancodes.from_string(str(keys))
        for key_codes in keys:
            if isinstance(key_codes[0], str):
                if key_codes[0] == 'wait':
                    time.sleep(1)

                continue

            self._virsh(
                ['send-key', node.id,
                ' '.join(map(lambda x: str(x), key_codes))])

    def _create_disk(self, name, capacity=1, pool='default', format='qcow2'):
        self._virsh(
            ['vol-create-as', '--pool', pool, '--name', name,
             '--capacity', capacity,'--format', format])

    def create_disk(self, disk):
        name = self._generate_disk_id(format=disk.format)
        if disk.base_image:
            base_name = disk.base_image.split('/')[-1]
            if not self.disk_exists(base_name):
                self._create_disk(base_name)
                self._virsh(
                    ['vol-upload', base_name, disk.base_image, '--pool',  'default'])
            capacity = self._get_volume_capacity(base_name)
            self._virsh(
                ['vol-create-as', '--name', name,  '--capacity', capacity,
                 '--pool', 'default', '--format', disk.format,
                 '--backing-vol', base_name, '--backing-vol-format', 'qcow2'])
        else:
            capacity = disk.size
            self._create_disk(name=name, capacity=capacity, format=disk.format)
        return self.get_disk_path(name)

    def delete_disk(self, disk):
        if disk.path is None:
            return
        self._virsh(['vol-delete',disk.path])

    def get_disk_path(self, name, pool='default'):
        command = self.virsh_cmd + ['vol-path', name, '--pool', pool]
        return subprocess.check_output(command).strip()

    def get_interface_addresses(self, interface):
        command = "arp -an | awk '$4 == \"%(mac)s\" && $7 == \"%(interface)s\" {print substr($2, 2, length($2)-2)}'" % {
            'mac': interface.mac_address,
            'interface': interface.network.bridge_name}
        output = subprocess.check_output(command)
        return [ipaddr.IPv4Address(s) for s in output.split()]

    def _virsh(self, param):
        command = self.virsh_cmd + param
        subprocess.check_call(command)

    def get_output_as_xml(self, command):
        output = subprocess.check_output(command)
        return xml.parse_string(output)

    def _init_capabilities(self):
        capabilities = self.get_output_as_xml(self.virsh_cmd + ['capabilities'])

        self.specs = []

        for guest in capabilities.find_all('guest'):
            for arch in guest.find_all('arch'):
                for domain in arch.find_all('domain'):
                    spec = DeploymentSpec()
                    spec.arch = arch['name']
                    spec.os_type = guest.find('os_type/text()')
                    spec.hypervisor = domain['type']
                    spec.emulator = (
                        domain.find('emulator') or arch.find('emulator')).text
                    self.specs.append(spec)

    def _generate_disk_id(self, prefix='disk', format='qcow2'):
        while True:
            id = prefix + '-' + str(int(time.time() * 100)) + '.%s' % format
            if not self.disk_exists(id):
                return id

    def _generate_network_id(self, name='net'):
        while True:
            id = name + '-' + str(int(time.time() * 100))
            if not self.network_exists(id):
                return id

    def _generate_node_id(self, name='node'):
        while True:
            id = name + '-' + str(int(time.time() * 100))
            if not self.node_exists(id):
                return id

    def is_node_defined(self, node):
        return self._system2(
            ' '.join(self.virsh_cmd) + " list --all | grep -q ' %s '" % node.id,
            expected_resultcodes=(0, 1)) == 0

    def is_node_running(self, node):
        return self._system2(
            ' '.join(self.virsh_cmd) + " list | grep -q ' %s '" % node.id,
            expected_resultcodes=(0, 1)) == 0

    def is_network_defined(self, network):
        return self._system2(
            ' '.join(self.virsh_cmd) + " net-list --all | grep -q '%s '" % network.id,
            expected_resultcodes=(0, 1)) == 0

    def is_network_running(self, network):
        return self._system2(
            ' '.join(self.virsh_cmd) + " net-list | grep -q '%s '" % network.id,
            expected_resultcodes=(0, 1)) == 0

    def get_all_defined_networks(self):
        output = subprocess.check_output(self.virsh_cmd + ['net-list', '--all'])
        return re.findall('(\S+).*active.*', output)

    def get_allocated_networks(self):
        allocated_networks = []
        all_networks = self.get_all_defined_networks()
        for network in all_networks:
            xml = self.get_output_as_xml(self.virsh_cmd + ['net-dumpxml', network])
            ip = xml.find('ip')
            network = ip.find('@address')
            prefix_or_netmask = ip.find('@prefix')
            if prefix_or_netmask is None:
                prefix_or_netmask = ip.find('@netmask')
            allocated_networks.append("%s/%s" % (network, prefix_or_netmask))
        return allocated_networks


    def _system2(self, command, expected_resultcodes=(0,)):
        logger.debug("Running %s" % command)

        commands = [i.strip() for i in re.split(ur'\|', command)]
        serr = []

        processes = [subprocess.Popen(
            shlex.split(commands[0]), stdin=None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)]
        for c in commands[1:]:
            processes.append(
                subprocess.Popen(
                    shlex.split(c), stdin=processes[-1].stdout,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE))

        processes[-1].wait()

        for p in processes:
            serr += [err.strip() for err in p.stderr.readlines()]

        returncode = processes[-1].returncode

        if expected_resultcodes and not returncode in expected_resultcodes:
            logger.error(
                "Command '%s' returned %d, stderr: %s" % (
                    command,
                    returncode, '\n'.join(serr)))
        else:
            logger.debug("Command '%s' returned %d" % (command, returncode))

        return returncode

    def _system(self, command, expected_resultcodes=(0,)):
        logger.debug("Running '%s'" % command)
        serr = []
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        process.wait()
        serr += [err.strip() for err in process.stderr.readlines()]

        if expected_resultcodes and not process.returncode in expected_resultcodes:
            logger.error(
                "Command '{0:>s}' returned {1:d}, stderr: {2:>s}".format(
                    command,
                    process.returncode, '\n'.join(serr)))
        else:
            logger.debug(
                "Command '{0:>s}' returned {1:d}".format(command,
                    process.returncode))

        return process.returncode
