Installing Fuel Web
===================

.. contents:: :local:

Instructions
------------

Fuel Web is being distributed as an ISO image, which contains an installer for an admin node. 

Once installed, Fuel Web can be used to deploy and manage OpenStack clusters. It will assign IP addresses to the nodes, perform PXE boot and initial configuration, and provision OpenStack nodes according to their roles in the cluster.

On Physical Hardware
--------------------

If you are going to install Fuel Web on physical hardware, you have to burn the provided ISO to a CD/DVD or USB stick and start the installation process by booting from this media, very much like any other OS.

After the installation is complete, you will need to allocate physical nodes for your OpenStack cluster, put them on the same L2 network and PXE boot from the admin node. They will get discovered in the UI and become available for installing OpenStack on them. 

On VirtualBox
-------------

If you are going to evaluate Fuel Web on VirtualBox, there is a very convenient way of doing this. We provide a set of scripts for VirtualBox, which will create and configure all the required VMs for you, including the admin node and slave nodes for OpenStack itself. It's a very simple, single-click installation.

The requirements are:

* physical machine with Linux or Mac OS, and VirtualBox installed
  * the scripts have been tested on Mac OS 10.7.5, Ubuntu 12.04 (the scripts do NOT support Windows-based platforms)
  * the scripts have been tested using VirtualBox 4.2.8

* Virtualbox must be installed with extension pack. It can be downloaded from the www.virtualbox.org.

* 8 GB+ of RAM

  * to handle 3 VMs for non-HA OpenStack installation (1 admin node, 1 controller node, 1 compute node) 
  * to handle 5 VMs for HA OpenStack installation (1 admin node, 3 controller nodes, 1 compute node) 

Automatic mode
^^^^^^^^^^^^^^

When you unpack the scripts, there will be the following important files:

* iso

  * this directory will initially be empty. if it does not exist, it has to be created
  * it needs to contain a single ISO image for Fuel Web. once you download ISO from the portal, put it into this directory

* config.sh

  * this file contains configuration which can be fine-tuned
  * for example, you can select how many virtual nodes to launch and how much memory to give them

* launch.sh

  * once executed, it will pick up an image from the "iso" directory, create a VM, mount the image to this VM, and automatically install admin node
  * after installation of the admin node, it will create slaves for OpenStack and PXE-boot them from the admin node
  * finally, it will give you the link to access Web-based UI on the admin node, so you can go there and start installation of an OpenStack cluster

Here is the example config file and the values that can be tweaked:

.. literalinclude:: /../virtualbox/config.sh
   :language: bash


Manual mode
^^^^^^^^^^^

Admin node deployment
~~~~~~~~~~~~~~~~~~~~~

1. Configure host-only intervare vboxnet0 in VirtualBox

  * IP address: 10.20.0.1
  * Interface mask: 255.255.255.0
  * No DHCP

2. Create VM for the admin node with the following parameters:

  * OS Type: Linux, Version: Red Hat (64bit)
  * RAM: 1024 MB
  * HDD: 16 GB, with dynamic disk expansion
  * CDROM: mount iso installer
  * Network 1: host-ony interface vboxnet0

3. Power on the VM in order to start the installation

4. Wait for welcome message with all information needed to login into the UI of Fuel Web

Adding slave nodes
~~~~~~~~~~~~~~~~~~

Create VMs with the following parameters:

* OS Type: Linux, Version: Red Hat (64bit)
* RAM: 768 MB
* HDD: 16 GB, with dynamic disk expansion
* Network 1: host-only interface vboxnet0

You should set priority for the network boot:

.. image:: _static/vbox-image1.png

Example of the network setup on VMs:

.. image:: _static/vbox-image2.png

Changing network parameters
---------------------------

This is an optional step. If you are going to use a different network, you can change the default network settings (10.20.0.2/24 gw 10.20.0.1).

In order to do so, press <TAB> аt the very first installation screen which says "Welcome to Fuel Web CentOS 6.3" and update kernel options. For example, to use 192.168.1.10/24 network with 192.168.1.1 as gateway and DNS server you should change the parameters to:

* vmlinuz initrd=initrd.img ks=cdrom:/ks.cfg ip=192.168.1.10 gw=192.168.1.1 dns1=192.168.1.1 netmask=255.255.255.0

After that press Enter and wait for the installation to complete.

