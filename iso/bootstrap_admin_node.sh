#!/bin/bash

function countdown() {
  local i
  sleep 1
  for ((i=$1-1; i>=1; i--)); do
    printf '\b\b%02d' "$i"
    sleep 1
  done
}
export LANG=en_US.UTF8
#export ADMIN_INTERFACE=eth0
# Be sure, that network devices have been initialized
udevadm trigger --subsystem-match=net
udevadm settle
# Take the very first ethernet interface, non-virtual, not a wireless
# Get the list of files sorted by "ls -vd" command
LIST_IF=$(ls -vd  /sys/class/net/*)
for DEV in $LIST_IF ; do
   # Take only links into account, skip files
   if test ! -L $DEV ; then
      continue
   fi
   DEVPATH=$(readlink -f $DEV)
   # Avoid virtual devices like loopback, tunnels, bonding, vlans ...
   case $DEVPATH in
        */virtual/*)
           continue
        ;;
   esac
   IF=${DEVPATH##*/}
   # Check ethernet only
   case "`cat $DEV/type`" in
        1)
        # TYPE=1 is ethernet, may also be wireless, bond, tunnel ...
        # Virtual lo, bounding, vlan, tunneling has been skipped before
        if test -d $DEV/wireless -o -L $DEV/phy80211 ;
        then
             continue
        else
        # Catch ethernet non-virtual device
             ADMIN_INTERFACE=$IF
             break
        fi
        ;;
        *) continue
        ;;
   esac
done
export ADMIN_INTERFACE

showmenu="no"
if [ -f /root/.showfuelmenu ]; then
  . /root/.showfuelmenu
fi
echo -n "Applying default Fuel settings..."
fuelmenu --save-only --iface=$ADMIN_INTERFACE
echo "Done!"
if [[ "$showmenu" == "yes" || "$showmenu" == "YES" ]]; then
  fuelmenu
  else
  #Give user 15 seconds to enter fuelmenu or else continue
  echo
  echo -n "Press a key to enter Fuel Setup (or press ESC to skip)... 15"
  countdown 15 & pid=$!
  if ! read -s -n 1 -t 15 key; then
    echo -e "\nSkipping Fuel Setup..."
  else
    { kill "$pid"; wait $!; } 2>/dev/null
    case "$key" in
      $'\e')  echo "Skipping Fuel Setup.."
              echo -n "Applying default Fuel setings..."
              fuelmenu --save-only --iface=$ADMIN_INTERFACE
              echo "Done!"
              ;;
      *)      echo -e "\nEntering Fuel Setup..."
              fuelmenu
              ;;
    esac
  fi
fi
#Reread /etc/sysconfig/network to inform puppet of changes
. /etc/sysconfig/network
hostname "$HOSTNAME"

# ruby21-hiera RPM does not include /var/lib/hiera/ directory which may cause errors
[ -d /var/lib/hiera ] || mkdir -p /var/lib/hiera
touch /var/lib/hiera/common.yaml /etc/puppet/hiera.yaml

# LANG variable is a workaround for puppet-3.4.2 bug. See LP#1312758 for details
puppet apply  /etc/puppet/modules/nailgun/examples/site.pp
bash /etc/rc.local
echo "Fuel node deployment complete!"
