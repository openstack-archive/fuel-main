#!/bin/bash

source config.sh

get_previous_networks() {
  virsh net-list | grep "$env_name_prefix" | awk '{print $1}'
}

define_network() {
  NAME=$1
  BRIDGE=$2
  IP=$3
  MASK=$4
  TMP_FILE="/tmp/tmp_fw_net.xml"
echo "Creating network template"
  cat <<EOF > ${TMP_FILE}
<network>
  <name>${NAME}</name>
  <forward mode="nat"/>
  <bridge name="${BRIDGE}" stp='on' delay='0' />
  <ip address="${IP}" netmask="${MASK}">
  </ip>
</network>
EOF
  virsh net-define ${TMP_FILE}
  virsh net-start ${NAME}
  virsh net-autostart ${NAME}
}


undefine_network() {
  NAME=$1
  virsh net-destroy ${NAME}
  virsh net-undefine ${NAME}
}

delete_previous_networks() {
  echo "checking existing nets"
  if get_previous_networks
  then
    for pnet in `get_previous_networks`
    do
      echo "Deleting net $pnet"
      undefine_network $pnet
    done
  fi
}

# example of network actions
#define_network testnet virbr100 10.99.1.1 255.255.255.0
#undefine_network testnet

check_existing_bridge() {
  BRIDGE=$1
  net_list=`virsh net-list | awk '{print $1}' | sed '1,2d'`
  #echo "This network located on you PC $net_list"

  #List bridge
  for net in $net_list
  do
        br_int=`virsh net-info $net | grep Bridge | awk '{print $2}'`
        if [ $br_int == $BRIDGE ]
        then
                echo "Bridge $BRIDGE already exists in $net network"
                exist_net+="$net "
        fi
  done
  for check_net in $exist_net
  do
        check_existing_vms $check_net
  done
}

check_existing_vms() {
  NET=$1
  LIST_VM=`grep -wr $NET /etc/libvirt/qemu | cut -d: -f 1 | cut -d"/" -f 5 | cut -d. -f 1 | sed '/networks/d'`
  echo "Network $NET is used by $LIST_VM VM"
}

#Check bridge create or not
check_all_bridges() {
  for idx1 in $idx_list
  do
        ip=`ip a show dev ${host_net_bridge[$idx1]}`
        if [ $? == 0 ]; then
                echo "Bridge exists"
                check_existing_bridge ${host_net_bridge[$idx1]}
                NET_ERR="True"
        fi
  done

  if [[ $NET_ERR ]]; then
        echo "ERROR: Some of bridges are already used, please check existing networks or redefine [idx] variable in config.sh"
        return 1
  else
        return 0
  fi
}

create_all_networks() {
  for idx1 in $idx_list
  do
        define_network ${host_net_name[$idx1]} ${host_net_bridge[$idx1]} ${host_nic_ip[$idx1]} ${host_nic_mask[$idx1]}
  done
}

#Modify default network for pxe boot
create_pxe_network() {
mkdir -p /var/lib/tftpboot
mkdir -p /mnt/fueliso
undefine_network default
gate=`echo $vm_master_ip | cut -d "." -f 1,2,3`
TMP_PXE="/tmp/tmp_pxe_net.xml"
echo "Creating network template"
cat <<EOF > ${TMP_PXE}
<network>
    <name>default</name>
    <bridge name="virbr0" />
    <forward />
    <ip address="$gate.1" netmask="$netmask">
        <tftp root="/var/lib/tftpboot"/>
        <dhcp>
            <range start="$vm_master_ip" end="$vm_master_ip" />
            <host mac="$mac" ip="$vm_master_ip" />
            <bootp file="pxelinux.0"/>
        </dhcp>
    </ip>
</network>
EOF
virsh net-define ${TMP_PXE}
virsh net-start default
virsh net-autostart default
}

#Adding NFS settings
nfs_setting_up() {
sed -i '/^\/var\/lib\/tftpboot/d' "/etc/exports"
cat <<EOF >> /etc/exports
/var/lib/tftpboot ${vm_master_ip}(ro,async,no_subtree_check,no_root_squash,crossmnt)
EOF
/etc/init.d/nfs-kernel-server restart
}

#settings up TFTP boot
tftpboot() {
tftpboot="memdisk  menu.c32  poweroff.com  pxelinux.0  reboot.c32"
for i in $tftpboot
do cp /usr/lib/syslinux/$i /var/lib/tftpboot/
done

#creation of default config pxelinux
mkdir -p /var/lib/tftpboot/pxelinux.cfg/
cat <<EOF > /var/lib/tftpboot/pxelinux.cfg/default
DEFAULT menu.c32
prompt 0
MENU TITLE My Distro Installer

TIMEOUT 300

LABEL localboot
MENU LABEL ^Local Boot
LOCALBOOT 0

LABEL fuel
MENU LABEL Install ^FUEL
MENU DEFAULT
KERNEL /fuel/isolinux/vmlinuz
INITRD /fuel/isolinux/initrd.img
APPEND biosdevname=0 ks=nfs:"$gate.1":/var/lib/tftpboot/fuel/ks.cfg repo=nfs:"$gate.1":/var/lib/tftpboot/fuel ip="$vm_master_ip" netmask="$netmask" gw="$gate.1" dns1="$gate.1"  showmenu=no ksdevice=eth0 installdrive=sda hostname=fuelweb.mirantis.com

LABEL reboot
MENU LABEL ^Reboot
KERNEL reboot.c32

LABEL poweroff
MENU LABEL ^Poweroff
KERNEL poweroff.com
EOF

#get images from ISO
mkdir -p /var/lib/tftpboot/fuel
cp $iso_path /var/lib/tftpboot/fuel
mount -o loop $iso_path /mnt/fueliso
rsync -a /mnt/fueliso/ /var/lib/tftpboot/fuel/
umount /mnt/fueliso && rmdir /mnt/fueliso
}
