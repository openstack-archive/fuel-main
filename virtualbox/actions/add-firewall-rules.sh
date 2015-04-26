#!/bin/bash

#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

#
# This script performs initial check and configuration IP forwarding on the
# host system. Need run this scripts with root privileges
#

host_nat_network0=$1
host_nat_network1=$2
host_nat_network2=$3

if [[ $(whoami) != "root" ]]; then
    echo "You are not root :("
    echo "You can use the following command \"./actions/enable-ip-forwarding.sh\" from \"virtualbox\" folder. Aborting..."
    exit 1
fi

if [[ "$(uname)" == "Linux" ]]; then
    echo "Setting masquerading configuration"
    if [ ! -x /sbin/iptables ] ; then
        echo -n "iptables is not available in the system path"
        exit 1
    else
        # Networks to masquerade in iptables
        host_nat_network1=(`echo $host_nat_network1 | sed 's/.$/0/'`)
        host_nat_network2=(`echo $host_nat_network2 | sed 's/.$/0/'`)
        # Add net.ipv4.ip_forward=1 into /etc/sysctl.conf
        cat /etc/sysctl.conf | grep "^net.ipv4.ip_forward=1" >/dev/null 2>&1
        if [ $? -eq 1 ]; then
            cat /etc/sysctl.conf | sed 's/^net.ipv4.ip_forward=.*/net.ipv4.ip_forward=1/g' > /etc/sysctl.conf_new
            rule=$(cat /etc/sysctl.conf_new | grep ^net.ipv4.ip_forward)
            if [[ "$rule" == "" ]]; then
                echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf_new
            fi
            mv /etc/sysctl.conf /etc/sysctl.conf_`date +%Y%m%d_%H%M%S`
            mv /etc/sysctl.conf_new /etc/sysctl.conf
        fi
        # Check and add iptables rules
        /sbin/iptables -L -n -t nat | grep $host_nat_network1
        if [ $? -eq 1 ]; then
            /sbin/iptables -t nat -A POSTROUTING -o $(ip r | grep default | cut -f5 -d ' ') -s $host_nat_network1/24  ! -d $host_nat_network1/24 -j MASQUERADE >/dev/null 2>&1
        fi
        /sbin/iptables -L -n -t nat | grep $host_nat_network2
        if [ $? -eq 1 ]; then
            /sbin/iptables -t nat -A POSTROUTING -o $(ip r | grep default | cut -f5 -d ' ') -s $host_nat_network2/24  ! -d $host_nat_network2/24 -j MASQUERADE >/dev/null 2>&1
        fi
        echo "1" > /proc/sys/net/ipv4/ip_forward
        # Save iptables rules for Ubuntu or Centos
        if [ -e /sbin/iptables-save ]; then
            /sbin/iptables-save | sudo tee /etc/iptables.rules >/dev/null 2>&1
            echo "#!/bin/sh" > /etc/network/if-pre-up.d/iptables
            echo "/sbin/iptables-restore < /etc/iptables.rules" >> /etc/network/if-pre-up.d/iptables
            echo "exit 0" >> /etc/network/if-pre-up.d/iptables
            echo "#!/bin/sh" > /etc/network/if-post-down.d/iptables
            echo "/sbin/iptables-save -c > /etc/iptables.rules" >> /etc/network/if-post-down.d/iptables
            echo "if [ -f /etc/iptables.rules ]; then" >> /etc/network/if-post-down.d/iptables
            echo "/sbin/iptables-restore < /etc/iptables.rules" >> /etc/network/if-post-down.d/iptables
            echo "fi" >> /etc/network/if-post-down.d/iptables
            echo "exit 0" >> /etc/network/if-post-down.d/iptables
            sudo chmod +x /etc/network/if-post-down.d/iptables
            sudo chmod +x /etc/network/if-pre-up.d/iptables
        elif [ -e /etc/init.d/iptables ]; then
            /etc/init.d/iptables save >/dev/null 2>&1
        fi
    fi
elif [[ "$(uname)" == "Darwin" ]]; then
    echo "Setting masquerading configuration"
    # Get default routed interface
    IF=$(route get default | grep interface | cut -d: -f2 | tr -d ' ')
    # Get vbox networks name
    vboxnet=$(ifconfig | grep vboxnet | awk '{print $1}'| sed 's/.$//')
    # Check and add rules into pf.conf
    cat /etc/pf.conf | grep "^nat on $IF inet from ! ($IF) to any -> ($IF)"  >/dev/null 2>&1
    if [ $? -eq 1 ]; then
        cp -f /etc/pf.conf /etc/pf.conf.`date +%Y%m%d_%H%M%S`
        echo "nat on $IF inet from ! ($IF) to any -> ($IF)" >> /etc/pf.conf
    fi
    for interface in $vboxnet; do
        vbox_iface="pass in on "$interface
        cat /etc/pf.conf | grep "$vbox_iface" >/dev/null 2>&1
        if [ $? -eq 1 ]; then
            echo $vbox_iface >> /etc/pf.conf
        fi
    done
    # Enable IP forwarding
    sysctl -wq net.inet.ip.forwarding=1
    sysctl -wq net.inet.ip.fw.enable=1
    # Activate PF rules
    pfctl -ef /etc/pf.conf
fi
