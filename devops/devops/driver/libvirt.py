# vim: ts=4 sw=4 expandtab

import os
import tempfile
import time
from collections import deque
from devops import xml
from devops import scancodes
from xmlbuilder import XMLBuilder
import ipaddr

def index(p, seq):
    for i in xrange(len(seq)):
        if p(seq[i]): return i
    return -1

def find(p, seq):
    for item in seq:
        if p(item): return item
    return None

class DeploymentSpec:
    def __repr__(self):
        return "<DeploymentSpec arch=\"%s\" os_type=\"%s\" hypervisor=\"%s\" emulator=\"%s\">" % (self.arch, self.os_type, self.hypervisor, self.emulator)

class LibvirtException(Exception): pass

class NetworkAllocator:
    netprefix = 26
    network_defaults = [ '10.0.0.0/8', '172.16.0.0/16', '192.168.0.0/16' ]
    def __init__(self, netprefix=None, nets=None):
        if netprefix is not None:
            self.netprefix = netprefix
        if nets is None:
            nets = self.network_defaults
        self.netranges = [ ipaddr.IPv4Network(ip) for ip in nets ]
        self.netranges.sort()
        self.nets = {}
        self.maxip = ipaddr.IPv4Address('0.0.0.0')
    def allocate(self, num):
        foruse = num + 3
        while foruse > 2**(32 - self.netprefix):
            self.netprefix -= 1
        for n1 in self.netranges:
            for n2 in n1.iter_subnets(new_prefix=self.netprefix):
                if n2.ip <= self.maxip:
                    continue
                self.maxip = n2.broadcast
                return n2

class LibvirtXMLBuilder:
    network_allocator = NetworkAllocator()

    def build_network_xml(self, network):
        network_xml = XMLBuilder('network')
        network_xml.name(network.id)
        dhcp = network_xml.dhcp()
        # XXX: FIX THIS
        NETWORKS_FROM_CONFIGURATION = 100
        alloc = self.network_allocator.allocate(NETWORKS_FROM_CONFIGURATION)
        hosts = list(alloc.iterhosts())
        mainip = str(hosts[0])
        start = str(hosts[1])
        end = str(hosts[-1])
        dhcp.range(start=start, end=end)
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
                node_xml.graphics(type='vnc', autoport='yes')

        return str(node_xml)


class Libvirt:
    def __init__(self, xml_builder = LibvirtXMLBuilder()):
        self.xml_builder = xml_builder
        self._init_capabilities()

    def node_exists(self, node_name):
        return self._system("virsh dominfo '%s'" % node_name) == 0

    def network_exists(self, network_name):
        return self._system("virsh net-info '%s'" % network_name) == 0

    def create_network(self, network):
        if not hasattr(network, 'id') or network.id is None:
            network.id = self._generate_network_id(network.name)

        with tempfile.NamedTemporaryFile(delete=True) as xml_file:
            xml_file.write(self.xml_builder.build_network_xml(network))
            xml_file.flush()
            self._virsh("net-define '%s'", xml_file.name)

        with os.popen("virsh net-dumpxml '%s'" % network.id) as f:
            network_element = xml.parse_stream(f)

        network.bridge_name = network_element.find('bridge/@name')
        network.mac_address = network_element.find('mac/@address')

    def delete_network(self, network):
        self._virsh("net-undefine '%s'", network.id)

    def start_network(self, network):
        self._virsh("net-start '%s'", network.id)

    def stop_network(self, network):
        self._virsh("net-destroy '%s'", network.id)

    def create_node(self, node):
        spec = find(lambda s: s.arch == node.arch, self.specs)
        if spec is None:
            raise LibvirtException, "Can't create node %s: insufficient capabilities" % node.name

        if not hasattr(node, 'id') or node.id is None:
            node.id = self._generate_node_id(node.name)

        with tempfile.NamedTemporaryFile(delete=True) as xml_file:
            xml_file.write(self.xml_builder.build_node_xml(node, spec))
            xml_file.flush()
            self._virsh("define '%s'", xml_file.name)

        with os.popen("virsh dumpxml '%s'" % node.id) as f:
            domain = xml.parse_stream(f)

        for interface_element in domain.find_all('devices/interface[@type="network"]'):
            network_id = interface_element.find('source/@network')

            interface = find(lambda i: i.network.id == network_id, node.interfaces)
            if interface is None:
                continue

            interface.mac_address = interface_element.find('mac/@address')

    def delete_node(self, node):
        self._virsh("undefine '%s'", node.id)

    def start_node(self, node):
        self._virsh("start '%s'", node.id)

    def stop_node(self, node):
        self._virsh("destroy '%s'", node.id)

    def reset_node(self, node):
        self._virsh("reset '%s'", node.id)

    def reboot_node(self, node):
        self._virsh("reboot '%s'", node.id)

    def shutdown_node(self, node):
        self._virsh("stop '%s'", node.id)

    def send_keys_to_node(self, node, keys):
        keys = scancodes.from_string(str(keys))
        while len(keys) > 0:
            if isinstance(keys[0], str):
                if keys[0] == 'wait':
                    time.sleep(1)

                keys = keys[1:]
                continue

            key_batch = keys[:10]
            special_pos = index(lambda x: isinstance(x, str), key_batch)
            if special_pos != -1:
                key_batch = key_batch[:special_pos]

            keys = keys[len(key_batch):]

            self._virsh("send-key '%s' %s", node.id, ' '.join(map(lambda x: str(x), key_batch)))

    def create_disk(self, disk):
        f, disk.path = tempfile.mkstemp(prefix='disk-', suffix=(".%s" % disk.format))
        os.close(f)

        self._system("qemu-img create -f '%s' '%s' '%s' >/dev/null 2>&1" % (disk.format, disk.path, disk.size))

    def delete_disk(self, disk):
        if disk.path is None: return
        
        os.unlink(disk.path)

    def _virsh(self, format, *args):
        command = ("virsh " + format) % args
        return self._system(command)

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
            if self._virsh("net-dumpxml '%s'", id) != 0:
                return id
            
    def _generate_node_id(self, name='node'):
        while True:
            id = name + '-' + str(int(time.time()*100))
            if self._virsh("dumpxml '%s'", id) != 0:
                return id

    def _system(self, command):
        if not os.environ.has_key('VERBOSE') or os.environ['VERBOSE'] == '':
            command += " 1>/dev/null 2>&1"
        else:
            print("Executing '%s'" % command)

        return os.system(command)

