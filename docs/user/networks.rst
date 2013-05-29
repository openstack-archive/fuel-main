Understanding and configuring network
=====================================

.. contents:: :local:

A few types of network managers are used in OpenStack clusters: FlatDHCP, VlanManager and Quantum.
Current version of FuelWeb supports only first two (FlatDHCP and VlanManager), but the FUEL library supports all three of them.
For more information about how first two network managers work you can read here:

* `OpenStack Networking – FlatManager and FlatDHCPManager <http://www.mirantis.com/blog/openstack-networking-flatmanager-and-flatdhcpmanager/>`_
* `Openstack Networking for Scalability and Multi-tenancy with VlanManager <http://www.mirantis.com/blog/openstack-networking-vlanmanager/>`_


FlatDHCP Manager (multi-host scheme)
------------------------------------

OpenStack basics
^^^^^^^^^^^^^^^^
The main idea behind the flat network manager is to configure bridge (i.e. **br100**) on every compute
node and have one of the machine's host interfaces connected to it. Once virtual machine is launched 
its virtual interface is getting connected to that bridge as well. The only one bridge is used for all VMs
of all OpenStack projects, and it means that there is no L2 isolation between
virtual hosts even if they are owned by separated projects. For this reason it is called *flat* manager.

The simplest case here is as shown on the following diagram. Here **eth0** interface is used to
give network access to virtual machines while **eth1** interface is the management network interface.

 .. uml::
    node "Compute1" {
        [eth0\nVM] as compute1_eth0
        [eth1\nManagement] as compute1_eth1
        [vm0] as compute1_vm0
        [vm1] as compute1_vm1
        [br100] as compute1_br100
        compute1_br100 -up- compute1_eth0
        compute1_vm0 -up- compute1_br100
        compute1_vm1 -up- compute1_br100
    }

    node "Compute2" {
        [eth0\nVM] as compute2_eth0
        [eth1\nManagement] as compute2_eth1
        [vm0] as compute2_vm0
        [vm1] as compute2_vm1
        [br100] as compute2_br100
        compute2_br100 -up- compute2_eth0
        compute2_vm0 -up- compute2_br100
        compute2_vm1 -up- compute2_br100
    }

    node "Compute3" {
        [eth0\nVM] as compute3_eth0
        [eth1\nManagement] as compute3_eth1
        [vm0] as compute3_vm0
        [vm1] as compute3_vm1
        [br100] as compute3_br100
        compute3_br100 -up- compute3_eth0
        compute3_vm0 -up- compute3_br100
        compute3_vm1 -up- compute3_br100
    }

    compute1_eth0 -up- [L2 switch]
    compute2_eth0 -up- [L2 switch]
    compute3_eth0 -up- [L2 switch]
    compute1_eth1 .up. [L2 switch]
    compute2_eth1 .up. [L2 switch]
    compute3_eth1 .up. [L2 switch]


FuelWeb deployment schema
^^^^^^^^^^^^^^^^^^^^^^^^^

FuelWeb deploys OpenStack in FlatDHCP mode with so called **multi-host** feature enabled.
Without this feature enabled, network traffic from each VM would go through the single
gateway host, which basically becomes a SPoF. In enabled mode, each compute node becomes a
gateway for all the VMs running on the same compute host, providing a balanced networking solution.
In this case, if one of the computes goes down, the rest of the environment remains operational.

Current version of FuelWeb forces to use VLANs even for FlatDHCP network manager.
On the Linux host it is implemented in the way that not the physical network interfaces is
connected to the bridge, but the VLAN interface (i.e. **eth0.102**).

 .. uml::
    node "Compute1 Node" {
        [eth0] as compute1_eth0
        [eth0.101\nManagement] as compute1_eth0_101
        [eth0.102\nVM] as compute1_eth0_102
        [vm0] as compute1_vm0
        [vm1] as compute1_vm1
        [vm2] as compute1_vm2
        [vm3] as compute1_vm3
        [br100] as compute1_br100
        compute1_eth0 -down- compute1_eth0_101
        compute1_eth0 -down- compute1_eth0_102
        compute1_eth0_102 -down- compute1_br100
        compute1_br100 -down- compute1_vm0
        compute1_br100 -down- compute1_vm1
        compute1_br100 -down- compute1_vm2
        compute1_br100 -down- compute1_vm3
    }

    node "Compute2 Node" {
        [eth0] as compute2_eth0
        [eth0.101\nManagement] as compute2_eth0_101
        [eth0.102\nVM] as compute2_eth0_102
        [vm0] as compute2_vm0
        [vm1] as compute2_vm1
        [vm2] as compute2_vm2
        [vm3] as compute2_vm3
        [br100] as compute2_br100
        compute2_eth0 -down- compute2_eth0_101
        compute2_eth0 -down- compute2_eth0_102
        compute2_eth0_102 -down- compute2_br100
        compute2_br100 -down- compute2_vm0
        compute2_br100 -down- compute2_vm1
        compute2_br100 -down- compute2_vm2
        compute2_br100 -down- compute2_vm3
    }

    compute1_eth0 -up- [L2 switch]
    compute2_eth0 -up- [L2 switch]

Therefore all switch ports where compute nodes are connected must be configured as tagged (trunk) ports
with required vlans allowed (enabled, tagged). Virtual machines will communicate with each other on L2 even
if they are on different compute nodes. If the virtual machine sends IP packets to some different network,
then they will be routed on the host machine according to the routing table. Default route will point to the
gateway which was specified on networks tab in UI as a gateway for public network.


VLAN Manager
^^^^^^^^^^^^

OpenStack basics
^^^^^^^^^^^^^^^^

Vlan manager mode is more suitable for large scale clouds. The idea behind this mode is to separate
groups of virtual machines, owned by different projects, on L2 layer. It VLAN Manager it is done by
tagging IP frames, or simply speaking, by VLANs. It allows virtual machines inside the given project
to communicate with each other and not to see any traffic from VMs of other projects.
Switch ports must be configured as tagged (trunk) ports to allow this scheme to work.

.. uml::
    node "Compute1 Node" {
        [eth0] as compute1_eth0
        [eth0.101\nManagement] as compute1_eth0_101
        [vlan102\n] as compute1_vlan102
        [vlan103\n] as compute1_vlan103
        [vm0] as compute1_vm0
        [vm1] as compute1_vm1
        [vm2] as compute1_vm2
        [vm3] as compute1_vm3
        [br102] as compute1_br102
        [br103] as compute1_br103
        compute1_eth0 -down- compute1_eth0_101
        compute1_eth0 -down- compute1_vlan102
        compute1_eth0 -down- compute1_vlan103
        compute1_vlan102 -down- compute1_br102
        compute1_vlan103 -down- compute1_br103
        compute1_br102 -down- compute1_vm0
        compute1_br102 -down- compute1_vm1
        compute1_br103 -down- compute1_vm2
        compute1_br103 -down- compute1_vm3
    }

    node "Compute2 Node" {
        [eth0] as compute2_eth0
        [eth0.101\nManagement] as compute2_eth0_101
        [vlan102\n] as compute2_vlan102
        [vlan103\n] as compute2_vlan103
        [vm0] as compute2_vm0
        [vm1] as compute2_vm1
        [vm2] as compute2_vm2
        [vm3] as compute2_vm3
        [br102] as compute2_br102
        [br103] as compute2_br103
        compute2_eth0 -down- compute2_eth0_101
        compute2_eth0 -down- compute2_vlan102
        compute2_eth0 -down- compute2_vlan103
        compute2_vlan102 -down- compute2_br102
        compute2_vlan103 -down- compute2_br103
        compute2_br102 -down- compute2_vm0
        compute2_br102 -down- compute2_vm1
        compute2_br103 -down- compute2_vm2
        compute2_br103 -down- compute2_vm3
    }

    compute1_eth0 -up- [L2 switch]
    compute2_eth0 -up- [L2 switch]

FuelWeb deployment schema
^^^^^^^^^^^^^^^^^^^^^^^^^

One of the physical interfaces on each host has to be chosen to carry VM-to-VM traffic (fixed network),
and switch ports must be configured to allow tagged traffic to pass through. OpenStack Computes will
untag the IP packets and send them to the appropriate VMs.
Simplifying the configuration of VLAN Manager, there is no known limitation which FuelWeb could add
in this particular networking mode.

Making Configuration
--------------------

Scheme
^^^^^^

Once the networking mode is chosen (FlatDHCP / Vlan), it is required to configure equipment according
to this scheme. Diagram below shows example configuration.

.. image:: _static/flat.png

By default several predefined networks are used:

* **FuelWeb** network is used for internal FuelWeb communications only and PXE booting (untagged on the scheme);
* **Public** network is used to get access from virtual machines to outside, Internet or office network (vlan 101 on the scheme);
* **Floating** network is used to get access to virtual machines from outside (shared L2-interface with **Public** network, in this case it's vlan 101);
* **Management** network is used for internal OpenStack communications (vlan 102 on the scheme);
* **Storage** network is used for storage traffic (vlan 103 on the scheme);
* **Fixed** - one (for flat mode) or more (for vlan mode) virtual machines network(s) (vlan 104 on the scheme).

Switch
^^^^^^

FuelWeb can configure hosts, however switches configuration is still manual work.
Unfortunately the configuration steps and even the terminology used is different for different vendors,
so we will try to provide vendor-agnostic information on how should traffic flow and leave the
vendor-specific details on your own. We will still provide an example for Cisco switch.

First of all, it is required to configure access ports to allow non-tagged PXE booting connections
from all slave nodes to FuelWeb node. We refer this network as "admin" network, or "fuelweb".
FuelWeb master node uses eth0 interface to serve PXE requests by default in this network.
So, if unchanged, it is required to set the switch port for eth0 of FuelWeb in access mode.
We recommend to use eth0 interfaces of all other nodes for PXE booting as well, and corresponding ports
must be in access mode top.
Taking into account that this is the network for PXE booting, it is strictly required to not mix this
L2 segment with any other company's infrastructure. FuelWeb runs DHCP server and in case if there is
another company's DHCP on the same L2, both company's infrastructure and FuelWeb's will be messed up.
Also you need to configure each of the switch's ports connected
to nodes as an "STP Edge port" (or a "spanning-tree portfast trunk" according to Cisco terminology).
If you don't do that, DHCP timeout issues may occur.

When "admin" network is configured, it is enough for FuelWeb to operate. Other networks are required
for OpenStack environments, and currently all of these networks lives in VLANs over the one or multiple
physical interfaces on node. It means that switch should pass tagged traffic, and untagging is done
on Linux hosts. *For the sake of simplicity, all the VLANs specified on networks tab of FuelWeb UI
should be configured on switch ports, pointing to slave nodes, as tagged.* Of course, it is
possible to specify as tagged only certain ports for a certain nodes. For example, there is no
need to pass public network to Cinder hosts.

It is enough to deploy the OpenStack environment. However it will not be really usable because
there is no connection to other corporate networks yet. To make it, uplink port(s) should be
configured. One of the VLANs may carry office network. To provide the access to FuelWeb WebUI
from office network, any other free physical network interface on FuelWeb master node can be used
and configured according to the office network rules (static IP or DHCP). The same corporate
network segment can be used for public and floating ranges. In this case, it will be required
to provide in UI corresponding VLAN ID and IP ranges. One public IP per node will be used to SNAT
traffic out of the VMs network, and one or more floating addresses per VM instance to get
access to the VM from corporate network or even global Internet. To have a VM visible from
Internet is similar to have it visible from corporate network - corresponding IP ranges and VLAN IDs
must be specified for floating and public networks. Current limitation of FuelWeb is that the user
can use only the same L2 segment for both public and floating networks.

Example configuration for one of the ports on Cisco switch:
interface GigabitEthernet0/6               # switch port
description s0_eth0 jv                     # description
switchport trunk encapsulation dot1q       # enables VLANs
switchport trunk native vlan 262           # access port, untags VLAN 262
switchport trunk allowed vlan 100,102,104  # 100,102,104 VLANs are passed with tags
switchport mode trunk                      # specifies the special mode to allow tagged traffic
spanning­tree portfast trunk               # specifies this port as STP Edge port (to prevent DHCP timeout issues)

Router
^^^^^^

To make VMs accessing outside world it is required to have an IP address set on router in public network.
In examples provided, it is 240.0.1.1 in VLAN 101. FuelWeb has a special field on networking tab for
gateway address. As soon as deployment of OpenStack is started, network on nodes is reconfigured
to use this gateway IP as the default gateway.
If floating addresses are from other L3 network, then it is required to set IP (or even multiple
IPs if floating addresses are from more than one L3 network) for them on router as well.
Otherwise floating IPs on nodes will be inaccessible.


Admin Node
^^^^^^^^^^

During master node installation it is assumed that there is a recursive DNS service on 10.20.0.1.

If you want to make slave nodes able to resolve public names you need to change this default value to
point on actual DNS service. This value can be changed via text based dialog provided by anaconda.
It is implemented in anaconda kickstart in post install section. Slave nodes use DNS service running
on master node and provided by cobbler and it relays requests to the actual DNS service if it does
not have information about requested name.

Once master node is installed you have to power on all other nodes and go to the url http://10.20.0.2:8000.
Slave nodes will be booted in bootstrap mode via PXE and you will see notifications on user interface
about discovered nodes. Here is the point where you can configure your cluster. It is supposed that
on the network tab you choose configuration shown on the following figure.

.. image:: _static/web_network_tab.png


