#!/bin/bash

function countdown() {
  local i
  sleep 1
  for ((i=$1-1; i>=1; i--)); do
    printf '\b\b%02d' "$i"
    sleep 1
  done
}

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

# apply puppet
puppet apply -d -v /etc/puppet/modules/nailgun/examples/host-only.pp

### docker stuff
dockerctl="/root/fuel-dockerctl/dockerctl"
images_dir="/var/www/nailgun/docker/images"

# prepare our tools
tar -C /root/ -xzf /var/www/nailgun/fuel-dockerctl.tgz

#FIXME: move to puppet manifests
yum --quiet install -y lrzip

# extract images
mkdir -p $images_dir
rm -f $images_dir/*tar
lrzip -f -d -o "$images_dir" "$images_dir/fuel-images.tar.lrz"

# load docker images
for image in $images_dir/*tar ; do
    echo "Docker loading $image"
    cat "$image" | docker load
done

# clean up extracted images
rm -f $images_dir/*tar

# run containers
$dockerctl start all

