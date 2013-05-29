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
All nodes has to be connected to a switch
ports where "**FuelWeb**" vlan frames untagged (without vlan tags) and all other frames tagged (with vlan
tags). Vlans 101-104 must not be filtered on those ports. It is crucial to isolate all used vlans
from the rest of your network on L2 because in other case DHCP server on master node can send
invalid DHCP offers to DHCP clients inside your network and vise versa slave nodes can get invalid
DHCP offers from DHCP servers outside scheme. Also you need to configure each of the switch's ports connected
to nodes as an "STP Edge port" (or a "spanning-tree portfast trunk" according to Cisco terminology).
If you don't do that, some DHCP timeout issues can occur. Once master node is installed and slave nodes are
booted in bootstrap mode you are able to use "Network Verification" feature in order to check
validity of vlan configuration on L2 switch.

Router
^^^^^^

To make virtual machines able to get access to the outside of OpenStack cluster it is needed to configure
address 240.0.1.1 on the "**Public**" (vlan 101) router interface. Cluster nodes will use this address as
default gateway. In turn, to get access from the outside of cluster to virtual machine via, for example,
ssh you need to use "**Floating**" IP address which could be assigned to given virtual machine via OpenStack
dashboard. You also need to configure corresponding IP address 240.0.0.1 on the "**Floating**" (vlan 101)
router interface. Besides, to get access from the outside to http://10.20.0.2:8000 you also need to
configure gateway address 10.20.0.1 on "**FuelWeb**" vlan interface (untagged on the scheme). Private
OpenStack networks (vlans 102, 103, 104) should not be configured on router as they used completely
inside cluster.


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


