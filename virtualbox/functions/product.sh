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

ssh_options='-oConnectTimeout=5 -oStrictHostKeyChecking=no -oCheckHostIP=no -oUserKnownHostsFile=/dev/null -oRSAAuthentication=no -oPubkeyAuthentication=no'

wait_for_fuel_menu() {
    ip=$1
    username=$2
    password=$3
    prompt=$4

    echo "Waiting for Fuel Menu so it can be skipped. Please do NOT abort the script..."

    # Loop until master node gets successfully installed
    maxdelay=3000
    while ! skip_fuel_menu $ip $username $password "$prompt"; do
        sleep 5
        ((waited += 5))
        if (( waited >= maxdelay )); then
          echo "Installation timed out! ($maxdelay seconds)" 1>&2
          exit 1
        fi
    done
}

skip_fuel_menu() {
    ip=$1
    username=$2
    password=$3
    prompt=$4

    # Log in into the VM, see if Fuel Setup is running or puppet already started
    # Looks a bit ugly, but 'end of expect' has to be in the very beginning of the line
    result=$(
        expect << ENDOFEXPECT
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        send "pgrep 'fuelmenu|puppet';echo \"returns $?\"\r"
        expect "$prompt"
ENDOFEXPECT
    )
    if [[ "$result" =~ "returns 0" ]]; then
      echo "Skipping Fuel Setup..."
      expect << ENDOFEXPECT
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        send "killall -w -SIGUSR1 fuelmenu\r"
        expect "$prompt"
ENDOFEXPECT
      return 0
    else
      return 1
    fi
}

is_product_vm_operational() {
    ip=$1
    username=$2
    password=$3
    prompt=$4

    # Log in into the VM, see if Puppet has completed its run
    # Looks a bit ugly, but 'end of expect' has to be in the very beginning of the line
    result=$(
        expect << ENDOFEXPECT
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        send "grep 'Fuel node deployment' /var/log/puppet/bootstrap_admin_node.log\r"
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

    for line in $result; do
        IFS="${OIFS}"
        if [[ "$line" == Fuel*complete* ]]; then
            IFS="${NIFS}"
            return 0;
        elif [[ "$line" == Fuel*FAILED* ]]; then
            IFS="${NIFS}"
            echo "$line" 1>&2
            exit 1
        fi
        IFS="${NIFS}"
    done

    return 1
}

wait_for_product_vm_to_install() {
    ip=$1
    username=$2
    password=$3
    prompt=$4

    echo "Waiting for product VM to install. Please do NOT abort the script..."

    # Loop until master node gets successfully installed
    maxdelay=3000
    while ! is_product_vm_operational $ip $username $password "$prompt"; do
        sleep 5
        ((waited += 5))
        if (( waited >= maxdelay )); then
          echo "Installation timed out! ($maxdelay seconds)" 1>&2
          exit 1
        fi
    done
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
    interface_id=$(($5-1))   # Subtract one to get ethX index (0-based) from the VirtualBox index (from 1 to 4)
    gateway_ip=$6

    # Check for internet access on the host system
    echo -n "Checking for internet connectivity on the host system... "
    check_hosts=`echo google.com wikipedia.com | tr '  ' '\n'`
    case $(uname) in
        Linux | Darwin)
            for i in ${check_hosts} ; do
                ping_host=`ping -c 2 ${i} | grep %`
                ping_host_result+=$ping_host
            done
        ;;
        CYGWIN*)
            if [ ! -z "`type ping | grep system32`" ]; then
                for i in ${check_hosts} ; do
                    ping_host=`ping -n 5 ${i} | grep %`
                    ping_host_result+=$ping_host
                done
            elif [ ! -z "`type ping | grep bin`" ]; then
                for i in ${check_hosts} ; do
                    ping_host=`ping ${i} count 5 | grep %`
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
    if [ -f /etc/resolv.conf ]; then
      nameserver="$(grep '^nameserver' /etc/resolv.conf | grep -v 'nameserver\s\s*127.' | head -3)"
    fi
    if [ -z "$nameserver" -a -x /usr/bin/nmcli ]; then
      # Get DNS from network manager
      if [ -n "`LANG=C nmcli nm | grep \"running\s\+connected\"`" ]; then
        nameserver="$(nmcli dev list | grep 'IP[46].DNS' | sed -e 's/IP[46]\.DNS\[[0-9]\+\]:\s\+/nameserver /'| grep -v 'nameserver\s\s*127.' | head -3)"
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

    # Log in into the VM, configure and bring up the NAT interface, set default gateway, check internet connectivity
    # Looks a bit ugly, but 'end of expect' has to be in the very beginning of the line
    result=$(
        expect << ENDOFEXPECT
        spawn ssh $ssh_options $username@$ip
        expect "connect to host" exit
        expect "*?assword:*"
        send "$password\r"
        expect "$prompt"
        send "file=/etc/sysconfig/network-scripts/ifcfg-eth$interface_id\r"
        expect "$prompt"
        send "hwaddr=\\\$(grep HWADDR \\\$file)\r"
        expect "$prompt"
        send "uuid=\\\$(grep UUID \\\$file)\r"
        expect "$prompt"
        send "echo -e \"\\\$hwaddr\\n\\\$uuid\\nDEVICE=eth$interface_id\\nTYPE=Ethernet\\nONBOOT=yes\\nNM_CONTROLLED=no\\nBOOTPROTO=dhcp\\nPEERDNS=no\" > \\\$file\r"
        expect "$prompt"
        send "sed \"s/GATEWAY=.*/GATEWAY=\"$gateway_ip\"/g\" -i /etc/sysconfig/network\r"
        expect "$prompt"
        send "echo -e \"$nameserver\" > /etc/dnsmasq.upstream\r"
        expect "$prompt"
        send "sed \"s/DNS_UPSTREAM:.*/DNS_UPSTREAM: \\\$(grep \'^nameserver\' /etc/dnsmasq.upstream | cut -d \' \' -f2)/g\" -i /etc/fuel/astute.yaml\r"
        expect "$prompt"
        send "sed -i 's/ONBOOT=no/ONBOOT=yes/g' /etc/sysconfig/network-scripts/ifcfg-eth1\r"
        expect "$prompt"
        send "sed -i 's/NM_CONTROLLED=yes/NM_CONTROLLED=no/g' /etc/sysconfig/network-scripts/ifcfg-eth1\r"
        expect "$prompt"
        send "sed -i 's/BOOTPROTO=dhcp/BOOTPROTO=static/g' /etc/sysconfig/network-scripts/ifcfg-eth1\r"
        expect "$prompt"
        send " echo \"IPADDR=$master_ip_pub_net\" >> /etc/sysconfig/network-scripts/ifcfg-eth1\r"
        expect "$prompt"
        send " echo \"NETMASK=$mask\" >> /etc/sysconfig/network-scripts/ifcfg-eth1\r"
        expect "$prompt"
        send "/sbin/iptables -t nat -A POSTROUTING -s $master_pub_net/24 \! -d $master_pub_net/24 -j MASQUERADE\r"
        expect "$prompt"
        send "service iptables save >/dev/null 2>&1\r"
        expect "$prompt"
        send "dockerctl restart cobbler >/dev/null 2>&1\r"
        expect "$prompt"
        send "service network restart >/dev/null 2>&1\r"
        expect "*OK*"
        expect "$prompt"
        send "dockerctl restart cobbler >/dev/null 2>&1\r"
        expect "$prompt"
        send "dockerctl check cobbler >/dev/null 2>&1\r"
        expect "*ready*"
        expect "$prompt"
        send "logout\r"
        expect "$prompt"
ENDOFEXPECT
    )

    # Waiting until the network services are restarted.
    # 5 seconds is optimal time for different operating systems.
    echo -e "\nWaiting until the network services are restarted..."
    sleep 5s
       result_inet=$(
            expect << ENDOFEXPECT
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

