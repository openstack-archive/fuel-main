Using VirtualBox to deploy nailgun and slave nodes.
===================================================

Nailgun server deployment
-------------------------

Nailgun server you should create VM with the following parameters:

* OS Type: Linux, Version: Red Hat (64bit)
* RAM: at least 512Mb, 1-2Gb recommended
* HDD: at least 10Gb, 20Gb recommended.
* Network: network interface should be connected to the network with slaves using internal network or virtual host-only adapter network. If you plan to deploy baremetal slave nodes you should choose bridge connection as the only available.

You should attach iso image with nailgun to the VM in settings.
After that you could poweron your VM.
When bootscreen was appeared you could change default network settings(10.20.0.2/24 gw 10.20.0.1) for nailgun server or you could do this at the end of install.Better to do that at the beginning otherwise you should watch out for dialog at the end of installation process and catch it to change network settings.
To change settings you should press <TAB> аt "Welcome to Nailgun CentOS 6.3" screen and change settings.
As example, you want to use 192.168.1.10/24 network for nailgun with 192.168.1.1 as gateway and DNS server you should change params to look like:
vmlinuz initrd=initrd.img ks=cdrom:/ks.cfg ip=192.168.1.10 gw=192.168.1.1 dns1=192.168.1.1 netmask=255.255.255.0.
Basically you could change only parameters that you need to change or don't change anything.
After that press Enter and wait for installation complete. When installation completed you will see "Welcome to the Nailgun server" with all information needed to login into the UI of Nailgun.

Slave nodes deployment
----------------------

For slave nodes you should create VMs with the following parameters:

* OS Type: Linux, Version: Red Hat (64bit)
* RAM: at least 1Gb, >2Gb recommended
* HDD: at least 20Gb,>50Gb recommended.
* Network: network interface should be connected to the network with nailgun using internal network or virtual host-only adapter network. If you plan to deploy baremetal slave nodes you should choose use bridge connection on nailgun!

You should select for nodes network boot as that 1-st method to use.

.. image:: _static/vbox-image1.png

Network setup on VM's
---------------------
Example of network setup on nodes/nailgun VM's.

.. image:: _static/vbox-image2.png
