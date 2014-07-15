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
showmenu="no"
if [ -f /root/.showfuelmenu ]; then
  . /root/.showfuelmenu
fi
echo -n "Applying default Fuel settings..."
fuelmenu --save-only --iface=eth0
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
              fuelmenu --save-only --iface=eth0
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
#Update motd for IP
primary="$(grep "interface:" /etc/fuel/astute.yaml | cut -d':' -f2 | tr -d ' ')"
echo "sed -i \"s%\(^.*able on:\).*$%\1 http://\`ip address show $primary | awk '/inet / {print \$2}' | cut -d/ -f1 -\`:8000%\" /etc/issue" >>/etc/rc.local
sed -i "s%\(^.*able on:\).*$%\1 http://`ip address show $primary | awk '/inet / {print \$2}' | cut -d/ -f1 -`:8000%" /etc/issue
# ruby21-hiera RPM does not include /var/lib/hiera/ directory which may cause errors
[ -d /var/lib/hiera ] || mkdir -p /var/lib/hiera
touch /var/lib/hiera/common.yaml /etc/puppet/hiera.yaml

# LANG variable is a workaround for puppet-3.4.2 bug. See LP#1312758 for details
puppet apply  /etc/puppet/modules/nailgun/examples/site.pp
echo "Fuel node deployment complete!"
