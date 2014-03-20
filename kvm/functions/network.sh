#!/bin/bash

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

 
