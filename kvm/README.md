In order to successfully run Mirantis OpenStack under KVM, you need to:
    
    download additional script images:
    http://srv11-msk.msk.mirantis.net/cloud-images/vmlinuz 
    http://srv11-msk.msk.mirantis.net/cloud-images/initrd.img
    and put its under 'kvm/images/pxeboot/' directory
    download the official release (.iso) and place it under 'iso' directory
    run "sudo ./launch.sh". it will automatically pick up the iso, and will spin up master node and slave nodes

If there are any errors, the script will report them and abort.

If you want to change settings (number of OpenStack nodes, CPU, RAM, HDD), please refer to "config.sh".

