# vim: ts=4 sw=4 expandtab

import os
import tempfile
import time
import subprocess, shlex
from collections import deque
from devops import xml
from devops import scancodes
from xmlbuilder import XMLBuilder
import ipaddr
import re

import logging
logger = logging.getLogger('devops.libvirt')

def index(p, seq):
    for i in xrange(len(seq)):
        if p(seq[i]): return i
    return -1

def find(p, seq):
    for item in seq:
        if p(item): return item
    return None

def spec_priority(spec):
    if spec.hypervisor == 'qemu':
        return 0.5
    return 1.0

class DeploymentSpec:
    def __repr__(self):
        return "<DeploymentSpec arch=\"%s\" os_type=\"%s\" hypervisor=\"%s\" emulator=\"%s\">" % (self.arch, self.os_type, self.hypervisor, self.emulator)

class LibvirtException(Exception): pass

class LibvirtXMLBuilder:

    def build_network_xml(self, network):
        network_xml = XMLBuilder('network')
        network_xml.name(network.id)
        network_xml.forward(mode='nat')
        
        if hasattr(network, 'ip_addresses') and not network.ip_addresses is None:
            with network_xml.ip(address=str(network.ip_addresses[1]), prefix=str(network.ip_addresses.prefixlen)):
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
                            end = network.ip_addresses[network.ip_addresses.numhosts-2]

                        network_xml.range(start=str(start), end=str(end))
                        for interface in network.interfaces:
                            address = find(lambda ip: ip in network.ip_addresses, interface.ip_addresses)
                            if address and interface.mac_address:
                                network_xml.host(mac=str(interface.mac_address), ip=str(address), name=interface.node.name)
                        if network.pxe:
                            network_xml.bootp(file="pxelinux.0")

        return str(network_xml)

    def build_node_xml(self, node, spec):
        node_xml = XMLBuilder("domain", type=spec.hypervisor)
        node_xml.name(node.id)
        node_xml.vcpu(str(node.cpu))
        node_xml.memory(str(node.memory*1024), unit='KiB')

        with node_xml.os:
            node_xml.type(spec.os_type, arch=node.arch)
            for boot_dev in node.boot:
                if boot_dev == 'disk':
                    node_xml.boot(dev="hd")
                else:
                    node_xml.boot(dev=boot_dev)

        ide_disk_names = deque(['hd'+c for c in list('abcdefghijklmnopqrstuvwxyz')])
        serial_disk_names = deque(['sd'+c for c in list('abcdefghijklmnopqrstuvwxyz')])

        
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
                    node_xml.driver(name="qemu", type=disk.format)
                    node_xml.source(file=disk.path)
                    node_xml.target(dev=disk_name(disk.bus), bus=disk.bus)

            if node.cdrom:
                with node_xml.disk(type="file", device="cdrom"):
                    node_xml.driver(name="qemu", type="raw")
                    node_xml.source(file=node.cdrom.isopath)
                    node_xml.target(dev=disk_name(node.cdrom.bus), bus=node.cdrom.bus)

            for interface in node.interfaces:
                with node_xml.interface(type="network"):
                    node_xml.source(network=interface.network.id)
            
            if node.vnc:
                node_xml.graphics(type='vnc', listen='0.0.0.0', autoport='yes')

        return str(node_xml)


class Libvirt:
    def __init__(self, xml_builder = LibvirtXMLBuilder()):
        self.xml_builder = xml_builder
        self._init_capabilities()

    def node_exists(self, node_name):
        return self._system("virsh dominfo '%s'" % node_name, expected_resultcodes=(0, 1)) == 0

    def network_exists(self, network_name):
        return self._system("virsh net-info '%s' 2>/dev/null" % network_name, expected_resultcodes=(0, 1)) == 0

    def create_network(self, network):
        if not hasattr(network, 'id') or network.id is None:
            network.id = self._generate_network_id(network.name)
        elif self.is_network_defined(network):
            self._virsh("net-undefine '%s'", network.id)

        with tempfile.NamedTemporaryFile(delete=True) as xml_file:
            network_xml = self.xml_builder.build_network_xml(network)
            logger.debug("libvirt: Building network with following XML:\n%s" % network_xml)
            xml_file.write(network_xml)
            xml_file.flush()
            self._virsh("net-define '%s'", xml_file.name)

        with os.popen("virsh net-dumpxml '%s'" % network.id) as f:
            network_element = xml.parse_stream(f)

        network.bridge_name = network_element.find('bridge/@name')
        network.mac_address = network_element.find('mac/@address')

    def delete_network(self, network):
        if self.is_network_defined(network):
            logger.debug("Network %s is defined. Undefining.")
            self._virsh("net-undefine '%s'", network.id)


    def start_network(self, network):
        if not self.is_network_running(network):
            logger.debug("Network %s is not running. Starting.")
            self._virsh("net-start '%s'", network.id)

    def stop_network(self, network):
        if self.is_network_running(network):
            logger.debug("Network %s is running. Stopping.")
            self._virsh("net-destroy '%s'", network.id)

    def _get_node_xml(self, node):
        with os.popen("virsh dumpxml '%s'" % node.id) as f:
            return xml.parse_stream(f)

    def create_node(self, node):
        specs = filter(lambda spec: spec.arch == node.arch, self.specs)
        if len(specs) == 0:
            raise LibvirtException, "Can't create node %s: insufficient capabilities" % node.name

        specs.sort(key=spec_priority)
        spec = specs[-1]

        if not hasattr(node, 'id') or node.id is None:
            node.id = self._generate_node_id(node.name)

        with tempfile.NamedTemporaryFile(delete=True) as xml_file:
            node_xml = self.xml_builder.build_node_xml(node, spec)
            logger.debug("libvirt: Building node with following XML:\n%s" % node_xml)
            xml_file.write(node_xml)
            xml_file.flush()
            self._virsh("define '%s'", xml_file.name)

        domain = self._get_node_xml(node)

        for interface_element in domain.find_all('devices/interface[@type="network"]'):
            network_id = interface_element.find('source/@network')

            interface = find(lambda i: i.network.id == network_id, node.interfaces)
            if interface is None:
                continue

            interface.mac_address = interface_element.find('mac/@address')

    def delete_node(self, node):
        if self.is_node_defined(node):
            logger.debug("Node %s defined. Undefining." % node.id)
            self._virsh("undefine '%s'", node.id)

    def start_node(self, node):
        if not self.is_node_running(node):
            logger.debug("Node %s is not running at the moment. Starting." % node.id)
            self._virsh("start '%s'", node.id)

        if node.vnc:
            domain = self._get_node_xml(node)

            port_text = domain.find('devices/graphics[@type="vnc"]/@port')
            if port_text: node.vnc_port = int(port_text)


    def stop_node(self, node):
        if self.is_node_running(node):
            logger.debug("Node %s is running at the moment. Stopping." % node.id)
            self._virsh("destroy '%s'", node.id)
            

    def reset_node(self, node):
        self._virsh("reset '%s'", node.id)

    def reboot_node(self, node):
        self._virsh("reboot '%s'", node.id)

    def shutdown_node(self, node):
        self._virsh("stop '%s'", node.id)


    def get_node_snapshots(self, node):
        command = "virsh snapshot-list '%s'" % node.id
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        if process.returncode != 0:
            logger.error("Command '%s' returned %d, stderr: %s" % (command, process.returncode, '\n'.join(serr)))
        else:
            logger.debug("Command '%s' returned %d" % (command, process.returncode))

        snapshot_ids = []
        for line in process.stdout.readlines()[2:]:
            if line.strip() == '': continue

            snapshot_ids.append(line.split()[0])

        return snapshot_ids

    def create_snapshot(self, node, description=None):
        snapshot_id = str(int(time.time()*100))

        with tempfile.NamedTemporaryFile(delete=True) as xml_file:
            snapshot_xml = XMLBuilder('domainsnapshot')
            snapshot_xml.name(snapshot_id)
            if description:
                snapshot_xml.description(description)

            logger.debug("Building snapshot with following XML:\n%s" % str(snapshot_xml))
            xml_file.write(str(snapshot_xml))
            xml_file.flush()

            self._virsh("snapshot-create '%s' '%s'", node.id, xml_file.name)

        return snapshot_id

    def revert_snapshot(self, node, snapshot_id=None):
        if not snapshot_id:
            snapshot_id = '--current'
        self._virsh("snapshot-revert '%s' %s", node.id, snapshot_id)

    def delete_snapshot(self, node, snapshot_id=None):
        if not snapshot_id:
            snapshot_id = '--current'
        self._virsh("snapshot-delete '%s' %s", node.id, snapshot_id)

    def send_keys_to_node(self, node, keys):
        keys = scancodes.from_string(str(keys))
        for key_codes in keys:
            if isinstance(key_codes[0], str):
                if key_codes[0] == 'wait':
                    time.sleep(1)

                continue

            self._virsh("send-key '%s' %s", node.id, ' '.join(map(lambda x: str(x), key_codes)))

    def create_disk(self, disk):
        if not disk.path:
            f, disk.path = tempfile.mkstemp(prefix='disk-', suffix=(".%s" % disk.format))
            os.close(f)

        if disk.base_image:
            self._system("qemu-img create -f '%(format)s' -b '%(backing_path)s' '%(path)s'" % {'format': disk.format, 'path': disk.path, 'backing_path': disk.base_image})
        else:
            self._system("qemu-img create -f '%(format)s' '%(path)s' '%(size)s'" % {'format': disk.format, 'path': disk.path, 'size': disk.size})


    def delete_disk(self, disk):
        if disk.path is None: return
        
        os.unlink(disk.path)

    def get_interface_addresses(self, interface):
        command = "arp -an | awk '$4 == \"%(mac)s\" && $7 == \"%(interface)s\" {print substr($2, 2, length($2)-2)}'" % { 'mac': interface.mac_address, 'interface': interface.network.bridge_name}
        with os.popen(command) as f:
            return [ipaddr.IPv4Address(s) for s in f.read().split()]

    def _virsh(self, format, *args):
        command = ("virsh " + format) % args
        logger.debug("libvirt: Running '%s'" % command)
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        if process.returncode != 0:
            logger.error("libvirt: command '%s' returned code %d:\n%s" % (command, process.returncode, process.stderr.read()))
            raise LibvirtException, "Failed to execute command '%s'" % command

    def _init_capabilities(self):
        with os.popen("virsh capabilities") as f:
            capabilities = xml.parse_stream(f)
        
        self.specs = []

        for guest in capabilities.find_all('guest'):
            for arch in guest.find_all('arch'):
                for domain in arch.find_all('domain'):
                    spec = DeploymentSpec()
                    spec.arch = arch['name']
                    spec.os_type = guest.find('os_type/text()')
                    spec.hypervisor = domain['type']
                    spec.emulator = (domain.find('emulator') or arch.find('emulator')).text

                    self.specs.append(spec)

    def _generate_network_id(self, name='net'):
        while True:
            id = name + '-' + str(int(time.time()*100))
            if not self.network_exists(id):
                return id
            
    def _generate_node_id(self, name='node'):
        while True:
            id = name + '-' + str(int(time.time()*100))
            if not self.node_exists(id):
                return id


    def is_node_defined(self, node):
        return self._system2("virsh list --all | grep -q ' %s '" % node.id, expected_resultcodes=(0, 1)) == 0

    def is_node_running(self, node):
        return self._system2("virsh list | grep -q ' %s '" % node.id, expected_resultcodes=(0, 1)) == 0

    def is_network_defined(self, network):
        return self._system2("virsh net-list --all | grep -q '%s '" % network.id, expected_resultcodes=(0, 1)) == 0

    def is_network_running(self, network):
        return self._system2("virsh net-list | grep -q '%s '" % network.id, expected_resultcodes=(0, 1)) == 0

    def _system2(self, command, expected_resultcodes=(0,)):
        logger.debug("libvirt: Running %s" % command)

        commands = [ i.strip() for i in re.split(ur'\|', command)]
        serr = []

        process = []
        process.append(subprocess.Popen(shlex.split(commands[0]), stdin=None, 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        for c in commands[1:]:
            process.append(subprocess.Popen(shlex.split(c), stdin=process[-1].stdout, 
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE))

        process[-1].wait()

        for p in process:
            serr += [ err.strip() for err in p.stderr.readlines() ]

        returncode = process[-1].returncode

        if expected_resultcodes and not returncode in expected_resultcodes:
            logger.error("libvirt: Command '%s' returned %d, stderr: %s" % (command, returncode, '\n'.join(serr)))
        else:
            logger.debug("libvirt: Command '%s' returned %d" % (command, returncode))

        return returncode

    def _system(self, command, expected_resultcodes=(0,)):
        logger.debug("libvirt: Running '%s'" % command)
        serr = []
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        serr += [ err.strip() for err in process.stderr.readlines() ]

        if expected_resultcodes and not process.returncode in expected_resultcodes:
            logger.error("libvirt: Command '%s' returned %d, stderr: %s" % (command, process.returncode, '\n'.join(serr)))
        else:
            logger.debug("libvirt: Command '%s' returned %d" % (command, process.returncode))

        return process.returncode

