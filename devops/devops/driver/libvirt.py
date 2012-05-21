# vim: ts=4 sw=4 expandtab

import os
import tempfile
from devops import xml
from xmlbuilder import XMLBuilder

def find(p, seq):
    for item in seq:
        if p(item): return item

class DeploymentSpec:
    pass

class LibvirtXMLBuilder:

    def build_network_xml(self, network):
        network_xml = XMLBuilder('network')
        network_xml.name(network.id)

        return str(network_xml)

    def build_node_xml(self, node, spec):
        # node_xml = XMLBuilder("domain", type="kvm")
        node_xml = XMLBuilder("domain", type=spec.hypervisor)
        node_xml.name(node.id)
        node_xml.memory(str(node.memory))

        with node_xml.os:
            node_xml.type("hvm", arch=node.arch)
            for boot_dev in node.boot:
                if boot_dev == 'disk':
                    node_xml.boot(dev="hd")
                else:
                    node_xml.boot(dev=boot_dev)

        with node_xml.devices:
            # node_xml.emulator("/usr/bin/kvm")
            node_xml.emulator(spec.emulator)

            if len(node.disks) > 0:
                node_xml.controller(type="ide")

            for disk in node.disks:
                with node_xml.disk(type="file", device="disk"):
                    node_xml.driver(name="qemu", type=disk.format)
                    node_xml.source(file=disk.path)

            for interface in node.interfaces:
                with node_xml.interface(type="network"):
                    node_xml.source(network=interface.network.id)
        
        return str(node_xml)


class Libvirt:
    def __init__(self, xml_builder = LibvirtXMLBuilder()):
        self.xml_builder = xml_builder
        self._init_capabilities()

    def node_exists(self, node_name):
        return os.system("virsh dominfo '%s'" % node_name) == 0

    def network_exists(self, network_name):
        return os.system("virsh net-info '%s'" % network_name) == 0

    def create_network(self, network):
        network.bridge_name = network.id
        if len(network.bridge_name) > 15:
          network.bridge_name = network.bridge_name[0:15]

        with tempfile.NamedTemporaryFile(delete=True) as xml_file:
            xml_file.write(self.xml_builder.build_network_xml(network))
            xml_file.flush()
            self._virsh("net-define '%s'", xml_file.name)

        with os.popen("virsh net-dumpxml '%s'" % network.id) as f:
            network_element = xml.parse_stream(f)

        # network.bridge_name = network_element.find('bridge/@name')
        network.mac_address = network_element.find('mac/@address')

    def delete_network(self, network):
        self._virsh("net-undefine '%s'", network.id)

    def start_network(self, network):
        self._virsh("net-start '%s'", network.id)

    def stop_network(self, network):
        self._virsh("net-destroy '%s'", network.id)

    def create_node(self, node):
        spec = DeploymentSpec()
        spec.hypervisor = "qemu"
        spec.emulator = "/usr/bin/qemu-system-x86_64"

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

    def create_disk(self, disk):
        f, disk.path = tempfile.mkstemp(prefix='disk-', suffix=(".%s" % disk.format))
        os.close(f)

        os.execute("qemu-img create -f '%s' '%s' '%s'" % (disk.format, disk.path, disk.size))

    def delete_disk(self, disk):
        if disk.path is None: return
        
        os.unlink(disk.path)

    def _virsh(self, format, *args):
        command = ("virsh " + format + " 1>/dev/null 2>&1") % args
        os.system(command)

    def _init_capabilities(self):
        with os.popen("virsh capabilities") as f:
            capabilities = xml.parse_stream(f)
        
        # for guest in doc.xpath('guest'):
        #     os_type = guest.find('os_type').text
            
