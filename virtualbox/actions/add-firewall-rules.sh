#!/bin/bash

#    Copyright 2015 Mirantis, Inc.
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
    echo
    echo "Setting up masquerading configuration..."
    type /sbin/iptables >/dev/null 2>&1
    if [ $? -eq 1 ]; then
        echo -n "iptables is not available in the system path"
        exit 1
    else
        # Networks to masquerade in iptables
        host_nat_network1=(`echo $host_nat_network1 | sed 's/.$/0/'`)
        host_nat_network2=(`echo $host_nat_network2 | sed 's/.$/0/'`)
        # Check iptables rules and informing the user about our next steps
        for i in {1..4}; do
            rules[$i]=""
        done
        /sbin/iptables -L -n -t nat | grep -q $host_nat_network1
        if [ $? -eq 1 ]; then
            rules[1]="sudo /sbin/iptables -t nat -A POSTROUTING -o $(ip r | grep default | cut -f5 -d ' ') -s $host_nat_network1/24  ! -d $host_nat_network1/24 -j MASQUERADE"
        fi
        /sbin/iptables -L -n -t nat | grep -q $host_nat_network2
        if [ $? -eq 1 ]; then
            rules[2]="sudo /sbin/iptables -t nat -A POSTROUTING -o $(ip r | grep default | cut -f5 -d ' ') -s $host_nat_network2/24  ! -d $host_nat_network2/24 -j MASQUERADE"
        fi
        sysctl net.ipv4.ip_forward | grep -q "net.ipv4.ip_forward = 1"
        if [ $? -eq 1 ]; then
            rules[3]="sudo sysctl net.ipv4.ip_forward=1"
        fi
        grep -R "^net.ipv4.ip_forward=1" /etc/sysctl.d/* >/dev/null 2>&1
        if [ $? -eq 1 ]; then
            rules[4]="sudo -i\necho \"net.ipv4.ip_forward=1\" > /etc/sysctl.d/77-fuel.conf; exit"
        fi
        if [[ ${rules[1]} != "" ]] || [[ ${rules[2]} != "" ]] || [[ ${rules[3]} != "" ]] || [[ ${rules[4]} != "" ]] ; then
            echo -e "We need to perform following commands to enable Internet access for the virtual machines:"
            for i in {1..4}; do
                if [[ ${rules[$i]} != "" ]]; then
                    echo -e ${rules[$i]}
                fi
            done
            echo
            read -p "Would you like to execute these commands automatically right now? (yes/no): " users_agree
            if [[ "$users_agree" == "y" ]] || [[ "$users_agree" == "Y" ]] || [[ "$users_agree" == "yes" ]]; then
                grep -R "^net.ipv4.ip_forward=1" /etc/sysctl.d/* >/dev/null 2>&1
                if [ $? -eq 1 ]; then
                    echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/77-fuel.conf
                fi
                # Check and add iptables rules
                /sbin/iptables -L -n -t nat | grep -q $host_nat_network1
                if [ $? -eq 1 ]; then
                    /sbin/iptables -t nat -A POSTROUTING -o $(ip r | grep default | cut -f5 -d ' ') -s $host_nat_network1/24  ! -d $host_nat_network1/24 -j MASQUERADE >/dev/null 2>&1
                fi
                /sbin/iptables -L -n -t nat | grep -q $host_nat_network2
                if [ $? -eq 1 ]; then
                    /sbin/iptables -t nat -A POSTROUTING -o $(ip r | grep default | cut -f5 -d ' ') -s $host_nat_network2/24  ! -d $host_nat_network2/24 -j MASQUERADE >/dev/null 2>&1
                fi
                # Enable IP forwarding
                sysctl net.ipv4.ip_forward=1 >/dev/null 2>&1
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
            elif [[ "$users_agree" == "n" ]] || [[ "$users_agree" == "N" ]] || [[ "$users_agree" == "no" ]]; then
                echo "Please execute the commands above manually. Also, please check that firewall rules will be loaded when you reboot your machine, and then execute the script again."
                echo "Aborting..."
                exit 1
            else
                echo "Wrong choice. Try again..."
                exit 1
            fi
        fi
    fi
elif [[ "$(uname)" == "Darwin" ]]; then
    echo
    echo "Setting up masquerading configuration..."
    # Get default routed interface
    IF=$(route get default | grep interface | cut -d: -f2 | tr -d ' ')
    # Get vbox networks name
    vboxnet=$(ifconfig | grep vboxnet | awk '{print $1}'| sed 's/.$//')
    # Check rules in /etc/pf.conf and informing the user about our next steps
    rules=0
    grep -q "^nat on $IF inet from ! ($IF) to any -> ($IF)" /etc/pf.conf >/dev/null 2>&1
    if [ $? -eq 1 ]; then
        rules=1
    fi
    for interface in $vboxnet; do
        vbox_iface="pass in on "$interface
        grep -q "$vbox_iface" /etc/pf.conf
        if [ $? -eq 1 ]; then
            rules=1
        fi
    done
    if [[ "$rules" == "1" ]]; then
        echo "We need to add following rules into configuration file /etc/pf.conf to enable Internet access for the virtual machines:"
        echo "nat on $IF inet from ! ($IF) to any -> ($IF)"
        for interface in $vboxnet; do
            grep -q $interface /etc/pf.conf >/dev/null 2>&1 
            if [ $? -eq 1 ]; then
                vbox_iface="pass in on "$interface
                echo $vbox_iface
            fi
        done
        read -p "Would you like to add these rules automatically right now? (yes/no): " users_agree
        if [[ "$users_agree" == "y" ]] || [[ "$users_agree" == "Y" ]] || [[ "$users_agree" == "yes" ]]; then
            # Create backup /etc/pf.conf
            curr_time=`date +%Y%m%d_%H%M%S`
            echo "Creating backup file /etc/pf.conf..."
            cp /etc/pf.conf /etc/pf.conf_$curr_time
            if [ -e /etc/pf.conf_$curr_time ]; then
                echo -e "Backup file" /etc/pf.conf_$curr_time "has been successfully completed\n"
            else
                echo "Cannot create backup file /etc/pf.conf... Aborting"
                exit 1
            fi
            # Add rules into configuration file /etc/pf.conf
            grep -q "^nat on $IF inet from ! ($IF) to any -> ($IF)" /etc/pf.conf >/dev/null 2>&1
            if [ $? -eq 1 ]; then
                sed -i '' '/dummynet-anchor "com.apple\/\*"/a\
                nat on '$IF' inet from ! ('$IF') to any -> ('$IF')
                ' /etc/pf.conf
            fi
            for interface in $vboxnet; do
                vbox_iface="pass in on "$interface
                grep -q "$vbox_iface" /etc/pf.conf >/dev/null 2>&1
                if [ $? -eq 1 ]; then
                    echo $vbox_iface >> /etc/pf.conf
                fi
            done
        elif [[ "$users_agree" == "n" ]] || [[ "$users_agree" == "N" ]] || [[ "$users_agree" == "no" ]]; then
            echo "Please add the rules above manually into the configuration file /etc/pf.conf, activate rules and then execute the script again. Aborting..."
            exit 1
        else
            echo "Wrong choice. Try again..."
            exit 1
        fi
    fi
    # Enable IP forwarding
    sysctl -w net.inet.ip.forwarding=1 >/dev/null 2>&1
    sysctl -w net.inet.ip.fw.enable=1 >/dev/null 2>&1
    # Activate PF rules
    pfctl -ef /etc/pf.conf
fi
