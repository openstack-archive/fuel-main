#!/bin/bash

function countdown() {
  local i
  sleep 1
  for ((i=$1-1; i>=1; i--)); do
    printf '..%02d' "$i"
    sleep 1
  done
}
export LANG=en_US.UTF8
showmenu="no"
bold=$(tput bold)
normal=$(tput sgr0)
red=$(tput setaf 1)
if [ -f /root/.showfuelmenu ]; then
  . /root/.showfuelmenu
fi
if [[ "$showmenu" == "yes" || "$showmenu" == "YES" ]]; then
  fuelmenu
  else
  #Give user 30 seconds to enter fuelmenu or else continue
  echo
  echo -n "${bold}${red}Press a key to enter Fuel Setup (or press ESC to skip)... 15"
  countdown 15 & pid=$!
  if ! read -s -n 1 -t 15 key; then
    echo "$normal"
    echo -e "\n${normal}Skipping Fuel Setup..."
    echo -n "Applying default Fuel setings..."
    fuelmenu --save-only --iface=eth0
    echo "Done!"
  else
    { kill "$pid"; wait $!; } 2>/dev/null
    echo "$normal"
    case "$key" in
      $'\e')  echo "Skipping Fuel Setup.."
              echo -n "Applying default Fuel setings..."
              fuelmenu --save-only --iface=eth0
              echo "Done!"
              ;;
      *)      echo -e "\n${normal}Entering Fuel Setup..."
              fuelmenu
              ;;
    esac
  fi
fi
#Reread /etc/sysconfig/network to inform puppet of changes
. /etc/sysconfig/network
hostname "$HOSTNAME"
#Update motd for IP
primary="$(grep mnbs_internal_interface= /etc/naily.facts | cut -d'=' -f2) "
echo "sed -i \"s%\(^.*able on:\).*$%\1 http://\`ip address show $primary | awk '/inet / {print \$2}' | cut -d/ -f1 -\`:8000%\" /etc/issue" >>/etc/rc.local
sed -i "s%\(^.*able on:\).*$%\1 http://`ip address show $primary | awk '/inet / {print \$2}' | cut -d/ -f1 -`:8000%" /etc/issue
# ruby21-hiera RPM does not include /var/lib/hiera/ directory which may cause errors
[ -d /var/lib/hiera ] || mkdir -p /var/lib/hiera
touch /var/lib/hiera/common.yaml /etc/puppet/hiera.yaml

# LANG variable is a workaround for puppet-3.4.2 bug. See LP#1312758 for details
puppet apply  /etc/puppet/modules/nailgun/examples/site.pp
echo "Fuel node deployment complete!"
