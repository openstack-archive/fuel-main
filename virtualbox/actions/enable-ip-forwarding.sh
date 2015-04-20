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
# host system.
#

source ./config.sh

# Check if root login via sudo su works, and save the password. Needed to
# setup accordingly some network configurations, like firewall and NAT
get_sudo_password() {
  echo -e "To configure NAT and Firewall, the script requires the sudo password"
  read -s -p "Enter your sudo password and wait (it won't be prompted): " PASSWORD
  result=$(expect <<ENDOFEXPECT
    spawn sudo su -
    expect "*assword*"
    send -- "$PASSWORD\r"
    expect "*\#*"
    send -- "whoami\r"
    expect "*\#*"
ENDOFEXPECT
  )
  for line in $result; do
    if [[ $line == *root* ]]; then
      echo "OK"
      SUDO_PASSWORD=$PASSWORD
      sudo -k
      return
    fi
  done
  echo "Your sudo password is not correct. Please retry"
  exit 1
}

# Requires sudo privileges for both Linux and Darwin
setup_host_masquerading_settings() {
  echo "Setting masquerading configuration"
  if [ "$(uname)" == "Linux" ]; then
    if [ ! -x /sbin/iptables ] ; then
        echo -n "iptables is not available in the system path"
        exit 1
      else
        # Networks to masquerade in iptables
        local host_nat_network1=(`echo $fuel_master_ips | awk '{print $2}' | sed 's/.$/0/'`)
        local host_nat_network2=(`echo $fuel_master_ips | awk '{print $3}' | sed 's/.$/0/'`)
        local rules=$(cat <<EOF
#!/bin/bash
\nsysctl -wq net.ipv4.conf.all.forwarding=1
\n/sbin/iptables -L -n -t nat | grep $host_nat_network1
\nif [ \$? -eq 1 ]; then
\n/sbin/iptables -t nat -A POSTROUTING -o $(ip r | grep default | cut -f5 -d ' ') -s $host_nat_network1/24  ! -d $host_nat_network1/24 -j MASQUERADE
\nfi
\n/sbin/iptables -L -n -t nat | grep $host_nat_network2
\nif [ \$? -eq 1 ]; then
\n/sbin/iptables -t nat -A POSTROUTING -o $(ip r | grep default | cut -f5 -d ' ') -s $host_nat_network2/24  ! -d $host_nat_network2/24 -j MASQUERADE
\nfi
EOF
)
        echo -e $rules > add_check_rules.sh
        chmod +x add_check_rules.sh

        local curr_dir=`pwd`
          result=$(expect <<ENDOFEXPECT
          spawn sudo su -
          expect "*assword*"
          send -- "$SUDO_PASSWORD\r"
          expect "*\#*"
          send -- "$curr_dir/add_check_rules.sh\r"
          expect "*\#*"
ENDOFEXPECT
        )
        echo "OK"
        rm $curr_dir/add_check_rules.sh
      fi
  elif [ "$(uname)" == "Darwin" ]; then
    # Default routed interface
      IF=$(route get default | grep interface | cut -d: -f2 | tr -d ' ')
      # Take the configuration of which interfaces to NAT
	  local vboxnet=""
	  local vbox_iface=""
	  vboxnet=$(ifconfig | grep vbox | awk '{print $1}'| sed 's/.$//')
	  for interface in $vboxnet; do
		  vbox_iface=$vbox_iface"\npass in on "$interface
	  done
      # Write pf.conf
      CONF=$(cat <<EOS
#FUEL
\nscrub-anchor "com.apple/*"
\nnat-anchor "com.apple/*"
\nrdr-anchor "com.apple/*"
\ndummynet-anchor "com.apple/*"
\nnat on $IF inet from ! ($IF) to any -> ($IF)
\nanchor "com.apple/*"
\nload anchor "com.apple" from "/etc/pf.anchors/com.apple"
$vbox_iface
\n#/FUEL
EOS
      )
      # Backup the system file and setup nat and PF
      echo -e $CONF > .pftmp
      result=$(expect <<ENDOFEXPECT
        spawn sudo su
        expect "*assword*"
        send -- "$SUDO_PASSWORD\r"
        expect "*\#*"
        send -- "sysctl -wq net.inet.ip.forwarding=1\r"
        expect "*\#*"
        send -- "sysctl -wq net.inet.ip.fw.enable=1\r"
        expect "*\#*"
        send -- "cp -f /etc/pf.conf /etc/pf.conf.`date +%Y%m%d_%H%M%S`\r"
        expect "*\#*"
        send -- "cat .pftmp > /etc/pf.conf\r"
        expect "*\#*"
        send -- "pfctl -ef /etc/pf.conf\r"
        expect "*\#*"
ENDOFEXPECT
        )
      rm -f .pftmp
      sudo -k
      echo "OK"
      rm -f .sudo_pwd
  elif [ "$(uname)" != "Cygwin" ]; then
    echo "$(uname) is not supported operating system."
    exit 1
  fi
}

# Clean the masquerading settings
clean_host_masquerading_settings() {
  echo "Cleaning masquerading configuration"
  if [ "$(uname)" == "Darwin" ]; then
    if [ -z /etc/pf.conf.bak ]; then
        result=$(expect <<ENDOFEXPECT
          spawn sudo su -
          expect "*assword*"
          send -- "$SUDO_PASSWORD\r"
          expect "*\#*"
          send -- "cp -f /etc/pf.conf.bak /etc/pf.conf\r"
          expect "*\#*"
          send -- "pfctl -ef /etc/pf.conf\r"
          expect "*\#*"
ENDOFEXPECT
          )
      fi
  fi
  echo "OK"
}

if [ "$(uname)" == "Linux" ]; then
  get_sudo_password
elif [ "$(uname)" == "Darwin" ]; then
  get_sudo_password
  clean_host_masquerading_settings
elif [ "$(uname)" != "Cygwin" ]; then
  echo "$(uname) is not supported operating system."
  exit 1
fi

# Clean up the eventual Fuel NAT on host system
setup_host_masquerading_settings
