#!/bin/bash
DEFAULT_GW=$1
ADMIN_IF=$(sed 's/\ /\n/g' /proc/cmdline | grep choose_interface | awk -F\= '{print $2}')
# Check if we do not already have static config (or interface seems unconfigured)
NETADDR=( $(ifconfig $ADMIN_IF | grep -oP "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}") )
if [ ! -z "$(grep $ADMIN_IF /etc/network/interfaces | grep dhcp)" ] ; then
	sed -i "/${ADMIN_IF}/d" /etc/network/interfaces
	echo 'include /etc/network/interfaces.d/*' >> /etc/network/interfaces
	echo -e "auto $ADMIN_IF\n$ADMIN_IF inet static\n\taddress ${NETADDR[0]}\n\tnetmask ${NETADDR[2]}\n\tbroadcast ${NETADDR[1]}\n\tgateway $DEFAULT_GW" > /etc/network/interfaces.d/ifcfg-"$ADMIN_IF"
fi
