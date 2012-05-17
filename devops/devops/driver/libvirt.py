import os
import tempfile
from xmlbuilder import XMLBuilder

class LibvirtXMLBuilder:

	def build_network_xml(self, network):
		network_xml = XMLBuilder('network')
		network_xml.name(network.name)
		network_xml.bridge(name=("bridge-%s" % network.name))

		return str(network_xml)

	def build_node_xml(self, node):
		node_xml = XMLBuilder("domain", type="kvm")
		node_xml.name(node.name)
		node_xml.memory(str(node.memory))

		with node_xml.os:
			node_xml.type("hvm", arch="x86_64")
			node_xml.boot(dev="network")
			node_xml.boot(dev="hd")

		with node_xml.features:
			node_xml.acpi
			node_xml.apic
			node_xml.pae

		node_xml.clock(offset="utc")
		node_xml.on_poweroff("destroy")
		node_xml.on_reboot("restart")
		node_xml.on_crash("restart")

		with node_xml.devices:
			node_xml.emulator("/usr/bin/kvm")
			node_xml.controller(type="ide")

			for disk in node.disks:
				with node_xml.disk(type="file", device="disk"):
					node_xml.driver(name="qemu", type="qcow2")
					node_xml.source(file=disk.path)

			for interface in node.interfaces:
				with node_xml.interface(type="network"):
					node_xml.source(network=interface.network.name)
		
		return str(node_xml)


class Libvirt:
    def __init__(self, xml_builder = LibvirtXMLBuilder()):
        self.xml_builder = xml_builder

    def create_network(self, network):
        # TODO: allocate uniq name
        with tempfile.NamedTemporaryFile(delete=True) as xml_file:
            xml_file.write(self._build_network_xml(network))
            xml_file.flush()
            self._virsh("net-define '%s'", xml_file.name)

    def delete_network(self, network):
        self._virsh("net-undefine '%s'", network.name)

    def start_network(self, network):
        self._virsh("net-start '%s'", network.name)

    def stop_network(self, network):
        self._virsh("net-destroy '%s'", network.name)

    def create_node(self, node):
        # TODO: allocate uniq name
        with tempfile.NamedTemporaryFile(delete=True) as xml_file:
            xml_file.write(self._build_node_xml(node))
            xml_file.flush()
            self._virsh("define '%s'", xml_file.name)
        pass

    def delete_node(self, node):
        self._virsh("undefine '%s'", node.name)

    def start_node(self, node):
        self._virsh("start '%s'", node.name)

    def stop_node(self, node):
        self._virsh("stop '%s'", node.name)

    def _virsh(self, format, *args):
        command = ("virsh " + format) % args
        os.system(command)

    def _build_network_xml(self, network):
        return self.xml_builder.build_network_xml(network)

    def _build_node_xml(self, node):
        return self.xml_builder.build_node_xml(node)

