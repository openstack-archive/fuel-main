#!/bin/bash

#    Copyright 2013 Mirantis, Inc.
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

# This file contains the functions for connecting to Fuel VM, checking if the installation process completed
# and Fuel became operational, and also enabling outbound network/internet access for this VM through the
# host system

source ./functions/shell.sh

ssh_options='-oConnectTimeout=5 -oStrictHostKeyChecking=no -oCheckHostIP=no -oUserKnownHostsFile=/dev/null -oRSAAuthentication=no -oPubkeyAuthentication=no'

wait_for_exec_in_bootstrap() {
    ip=$1
    username=$2
    password=$3
    prompt=$4
    cmd=$5

    # Log in into the VM, exec cmd and print exitcode
    # Looks a bit ugly, but 'end of expect' has to be in the very beginning of the line
    result=$(
        execute expect << ENDOFEXPECT
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        send "$cmd\r"
        expect "$prompt"
        send "echo \"rc=\$?\"\r"
        expect "$prompt"
        send "logout\r"
        expect "$prompt"
ENDOFEXPECT
    )
    echo "$result" | grep -q "[r]c=0" >&2 && return 0
    return 1
}

wait_for_product_vm_to_download() {
    ip=$1
    username=$2
    password=$3
    prompt=$4

    echo -n "Waiting for product VM to download files. Please do NOT abort the script... "

    # Loop until master node booted and wait_for_external_config started
    maxdelay=3000
    while ! wait_for_exec_in_bootstrap $ip $username $password "$prompt" "ps xa | grep '\[w\]ait_for_external_config'"; do
        sleep 5
        ((waited += 5))
        if (( waited >= maxdelay )); then
            echo "Installation timed out! ($maxdelay seconds)" 1>&2
            exit 1
        fi
    done

    echo "OK"
}

wait_for_product_vm_to_install() {
    ip=$1
    username=$2
    password=$3
    prompt=$4

    echo -n "Waiting for product VM to install. Please do NOT abort the script... "

    # Loop until master node gets successfully installed
    maxdelay=3000
    while wait_for_exec_in_bootstrap $ip $username $password "$prompt" "ps xa | grep '\[b\]ootstrap_admin_node.sh'"; do
        sleep 5
        ((waited += 5))
        if (( waited >= maxdelay )); then
            echo "Installation timed out! ($maxdelay seconds)" 1>&2
            exit 1
        fi
    done

    echo "OK"
}

check_internet_connection() {
    line=$1
    OIFS="${IFS}"
    NIFS=$' '
    IFS="${NIFS}"
    for i in $line; do
        if [[ "$i" == *% && "$i" != 100* ]]; then
            return 0
        fi
    done
    IFS="${OIFS}"
    return 1
}

enable_outbound_network_for_product_vm() {
    ip=$1
    username=$2
    password=$3
    prompt=$4

    # Check for internet access on the host system
    echo -n "Checking for internet connectivity on the host system... "
    check_hosts=`echo google.com wikipedia.com | tr '  ' '\n'`
    case $(execute uname) in
        Linux | Darwin)
            for i in ${check_hosts} ; do
                ping_host=`execute ping -c 2 ${i} | grep %`
                ping_host_result+=$ping_host
            done
        ;;
        CYGWIN*)
            if [ ! -z "`execute type ping | grep system32`" ]; then
                for i in ${check_hosts} ; do
                    ping_host=`execute ping -n 5 ${i} | grep %`
                    ping_host_result+=$ping_host
                done
            elif [ ! -z "`execute type ping | grep bin`" ]; then
                for i in ${check_hosts} ; do
                    ping_host=`execute ping ${i} count 5 | grep %`
                    ping_host_result+=$ping_host
                done
            else
                print_no_internet_connectivity_banner
            fi
        ;;
        *)
            print_no_internet_connectivity_banner
        ;;
    esac

    check_internet_connection "$ping_host_result"
    if [[ $? -eq 0 ]]; then
        echo "OK"
    else
        print_no_internet_connectivity_banner
    fi

    # Check host nameserver configuration
    echo -n "Checking local DNS configuration... "
    if execute test -f /etc/resolv.conf ; then
      nameserver="$(execute grep '^nameserver' /etc/resolv.conf | grep -v 'nameserver\s\s*127.' | head -3)"
    fi
    if [ -z "$nameserver" ] && execute test -x /usr/bin/nmcli; then
      # Get DNS from network manager
      if [ -n "`execute LANG=C nmcli nm | grep \"running\s\+connected\"`" ]; then
        nameserver="$(execute nmcli dev list | grep 'IP[46].DNS' | sed -e 's/IP[46]\.DNS\[[0-9]\+\]:\s\+/nameserver /'| grep -v 'nameserver\s\s*127.' | head -3)"
      fi
    fi
    if [ -z "$nameserver" ]; then
      echo "/etc/resolv.conf does not contain a nameserver. Using 8.8.8.8 for DNS."
      nameserver="nameserver 8.8.8.8"
    else
      echo "OK"
    fi

    # Enable internet access on inside the VMs
    echo -n "Enabling outbound network/internet access for the product VM... "

    # Get network settings (ip address and ip network) for eth1 interface of the master node
    local master_ip_pub_net=$(echo $fuel_master_ips | cut -f2 -d ' ')
    master_ip_pub_net="${master_ip_pub_net%.*}"".1"
    local master_pub_net="${master_ip_pub_net%.*}"".0"

    # Convert nameservers list into the one line separated by the comma
    dns_upstream="$(echo -e $nameserver | cut -d ' ' -f2 | sed -e':a;N;$!ba;s/\n/,/g')"

    # Log in into the VM, configure and bring up the NAT interface, set default gateway, check internet connectivity
    # Looks a bit ugly, but 'end of expect' has to be in the very beginning of the line
    result=$(
        execute expect << ENDOFEXPECT
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        # make backups, remove network manager options, disable defaults, enable boot and disable network manager
        send "sed -i.orig '/^UUID=\\\|^NM_CONTROLLED=/d;s/^\\\(.*\\\)=yes/\\\1=no/g;s/^ONBOOT=.*/ONBOOT=yes/;/^ONBOOT=/iNM_CONTROLLED=no' /etc/sysconfig/network-scripts/ifcfg-eth{0,1,2}\r"
        expect "$prompt"
        # eth1 should be static with private ip address and provided netmask
        send "sed -i 's/^BOOTPROTO=.*/BOOTPROTO=static/;/^BOOTPROTO/aIPADDR=${master_ip_pub_net}\\\nNETMASK=${mask}' /etc/sysconfig/network-scripts/ifcfg-eth1\r"
        expect "$prompt"
        # eth2 should get ip address via dhcp and used default route
        send "sed -i 's/^BOOTPROTO=.*/BOOTPROTO=dhcp/;s/^DEFROUTE=.*/DEFROUTE=yes/;/^BOOTPROTO/aPERSISTENT_DHCLIENT=yes' /etc/sysconfig/network-scripts/ifcfg-eth2\r"
        expect "$prompt"
        # make backup and disable zeroconf at all because we should use only DHCP on eth2
        send "sed -i.orig '/NOZEROCONF/d;aNOZEROCONF=yes' /etc/sysconfig/network\r"
        expect "$prompt"
        # remove default route from eth0 and system wide settings if exists
        send "sed -i '/^GATEWAY=/d' /etc/sysconfig/network /etc/sysconfig/network-scripts/ifcfg-eth0\r"
        expect "$prompt"
        # fix bug https://bugs.centos.org/view.php?id=7351
        send "sed -i.orig '/^DEVICE=lo/aTYPE=Loopback' /etc/sysconfig/network-scripts/ifcfg-lo\r"
        expect "$prompt"
        # remove old settings from the resolv.conf and dnsmasq.upstream if exists
        send "sed -i.orig '/^nameserver/d' /etc/resolv.conf /etc/dnsmasq.upstream &>/dev/null\r"
        expect "$prompt"
        # update the resolv.conf and dnsmasq.upstream with the new settings
        send "echo -e '$nameserver' | tee -a /etc/dnsmasq.upstream >>/etc/resolv.conf\r"
        expect "$prompt"
        # update the astute.yaml with the new settings
        send "sed -i.orig '/DNS_UPSTREAM/c\\"DNS_UPSTREAM\\": \\"${dns_upstream}\\"' /etc/fuel/astute.yaml\r"
        expect "$prompt"
        # enable NAT (MASQUERADE) and forwarding for the public network
        send "/sbin/iptables -t nat -A POSTROUTING -s $master_pub_net/24 \! -d $master_pub_net/24 -j MASQUERADE\r"
        expect "$prompt"
        send "/sbin/iptables -I FORWARD 1 --dst $master_pub_net/24 -j ACCEPT\r"
        expect "$prompt"
        send "/sbin/iptables -I FORWARD 1 --src $master_pub_net/24 -j ACCEPT\r"
        expect "$prompt"
        send "service iptables save &>/dev/null\r"
        expect "$prompt"
        # disable NetworkManager and apply the network changes
        send "nmcli networking off &>/dev/null ; service network restart &>/dev/null\r"
        expect "$prompt"
        send "logout\r"
        expect "$prompt"
ENDOFEXPECT
    )
    echo "OK"

    # Waiting until the network services are restarted.
    # 5 seconds is optimal time for different operating systems.
    echo -n "Waiting until the network services are restarted... "
    sleep 5s
    result_inet=$(
        execute expect << ENDOFEXPECT
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        send "for i in {1..5}; do ping -c 2 google.com || ping -c 2 wikipedia.com || sleep 2; done\r"
        expect "*icmp*"
        expect "$prompt"
        send "logout\r"
        expect "$prompt"
ENDOFEXPECT
    )

    # When you are launching command in a sub-shell, there are issues with IFS (internal field separator)
    # and parsing output as a set of strings. So, we are saving original IFS, replacing it, iterating over lines,
    # and changing it back to normal
    #
    # http://blog.edwards-research.com/2010/01/quick-bash-trick-looping-through-output-lines/
    OIFS="${IFS}"
    NIFS=$'\n'
    IFS="${NIFS}"

    for line in $result_inet; do
        IFS="${OIFS}"
        if [[ $line == *icmp_seq* ]]; then
        IFS="${NIFS}"
            echo "OK"
            wait_for_exec_in_bootstrap $ip $username $password "$prompt" "pkill -f ^wait_for_external_config"
            return 0;
        fi
        IFS="${NIFS}"
    done
    print_no_internet_connectivity_banner
    return 1
}

print_no_internet_connectivity_banner() {
    echo "FAIL"
    echo "############################################################"
    echo "# WARNING: some of the Fuel features will not be supported #"
    echo "#          because there is no Internet connectivity       #"
    echo "############################################################"
}
