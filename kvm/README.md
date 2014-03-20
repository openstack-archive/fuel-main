In order to successfully run Mirantis OpenStack under KVM, you need to:

*   download the official release (.iso) and place it under 'iso' directory
*   run ``sudo ./launch.sh``.it will automatically pick up the iso, and will spin up master node and
slave nodes

If there are any errors, the script will report them and stop doing anything.

Any settings (such as number of OpenStack nodes, CPU cores, RAM, HDD) could be changed in config.sh
