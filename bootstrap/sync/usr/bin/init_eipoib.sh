#!/bin/bash

# Constants
readonly ETH_IPOIB_INTERFACES='/sys/class/net/eth_ipoib_interfaces'
readonly SCOPE=`basename $0`

# This functions print logs to /var/log/messages
function logger_print () {
   priority=$1
   msg=$2
   logger -t $SCOPE "$priority: $msg"
}

function create_vlan(){
  eth_interface=$1
  ib_interface=$2
  current_vlan=$3
  current_mac=$4

  if [ "$current_vlan" == "0" ]; then
    current_vlan=""
    dec_vlan=""
    hex_vlan=""
  else
    shut_down_MSB=$(( ~0x8000 ))
    dec_vlan=$(( $shut_down_MSB & $current_vlan ))
    hex_vlan=".${current_vlan#0x}"
  fi

  ib_create_child_path="/sys/class/net/$ib_interafce/create_child"
  ib_delete_child_path="/sys/class/net/$ib_interafce/delete_child"
  eth_slaves_path="/sys/class/net/$eth_interface/eth/slaves"
  eth_vifs_path="/sys/class/net/$eth_interface/eth/vifs"
  ib_child="$ib_interface$hex_vlan.1"

  # TODO: Change check to vifs (currently vifs print is limited to 87)
  if ! grep -Fwq "$ib_child" $eth_slaves_path
  then

    if ip a | grep -wq "$ib_child"
    then
      echo "$current_vlan.1"  > $ib_delete_child_path
    fi

    logger_print info "Creating $ib_child $current_mac $dec_vlan"
    echo "$current_vlan.1"  > $ib_create_child_path && \
    ifconfig $eth_interface up && \
    echo "+$ib_child"  > $eth_slaves_path && \
    echo "+$ib_child" $current_mac $dec_vlan  > $eth_vifs_path && \
    sleep 0.2
  fi

}

function remove_vlan(){
  eth_interface=$1
  ib_interface=$2
  dec_vlan=$3
  mac=$4
  sm_vlans=`cat /sys/class/infiniband/$device/ports/$port/pkeys/* \
| grep -v 0xffff | grep -v 0x7fff | grep -v 0000`

  # Fixed paths
  ib_delete_child_path="/sys/class/net/$ib_interafce/delete_child"
  eth_slaves_path="/sys/class/net/$eth_interface/eth/slaves"
  eth_vifs_path="/sys/class/net/$eth_interface/eth/vifs"

  # Calculate VLAN
  current_vlan=`printf '0x%x\n' $(( 0x8000 + $dec_vlan ))`
  hex_vlan=".${current_vlan#0x}"
  ib_child="$ib_interface$hex_vlan.1"

  if [[ ! $sm_vlans =~ $current_vlan ]]
  then
    logger_print info "Creating $ib_child $current_mac $dec_vlan"
    echo "-$ib_child" $current_mac $dec_vlan  > $eth_vifs_path && \
    echo "-$ib_child"  > $eth_slaves_path
    echo "$current_vlan.1"  > $ib_delete_child_path
    sleep 0.1
  fi
}

function update(){
  # Read mapping lines of the form "eth0 over IB port: ib0"
  while read -r line
  do
    line_arr=( $line )
    eth_interface=${line_arr[0]}
    ib_interafce=${line_arr[4]}
    current_mac=`ip link show $eth_interface | grep link | awk '{print $2}'`

    # Create default VLAN
    vlan="0"
    create_vlan $eth_interface $ib_interafce $vlan $current_mac

    # Create VLANs parameters
    port_to_dev=( `ibdev2netdev |grep " $ib_interafce "` )
    device=${port_to_dev[0]}
    port=${port_to_dev[2]}
    sm_vlans=`cat /sys/class/infiniband/$device/ports/$port/pkeys/* \
| grep -v 0xffff | grep -v 0x7fff | grep -v 0000`
    configured_dec_vlans=`cat /sys/class/net/$eth_interface/eth/vifs \
| cut -d '=' -f 4 | grep -v 'N/A'`

    # Ensure supported VLANs
    for vlan in $sm_vlans;
    do
      create_vlan $eth_interface $ib_interafce $vlan $current_mac
    done

    # Delete unsupported VLANs
    for dec_vlan in $configured_dec_vlans;
    do
      remove_vlan $eth_interface $ib_interafce $dec_vlan $current_mac $sm_vlans
    done

  done < "$ETH_IPOIB_INTERFACES"
}

# Update PKEYs every 3 seconds
while :
do
  update
  sleep 3
done
