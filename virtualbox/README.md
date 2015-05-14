VirtualBox enviropment kit
==========================

Requirements
------------

- VirtualBox with VirtualBox Extension Pack
- procps
- expect
- Cygwin for Windows host PC
- Enable VT-x/AMD-V acceleration option on your hardware for 64-bits guests

Run
---

In order to successfully run Mirantis OpenStack under VirtualBox, you need to:
- download the official release (.iso) and place it under 'iso/' directory
- run "./launch.sh" (or "./launch\_8GB.sh" or "./launch\_16GB.sh" according to your system resources). It will automatically pick up the iso and spin up master node and slave nodes

If there are any errors, the script will report them and abort.

If you want to change settings (number of OpenStack nodes, CPU, RAM, HDD), please refer to "config.sh".

