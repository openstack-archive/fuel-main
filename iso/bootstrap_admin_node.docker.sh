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
# ruby21-hiera RPM does not include /var/lib/hiera/ directory which may cause errors
[ -d /var/lib/hiera ] || mkdir -p /var/lib/hiera
touch /var/lib/hiera/common.yaml /etc/puppet/hiera.yaml

### docker stuff
images_dir="/var/www/nailgun/docker/images"

# extract docker images
mkdir -p $images_dir $sources_dir
rm -f $images_dir/*tar
pushd $images_dir &>/dev/null

echo "Extracting and loading docker images. (This may take a while)"
lrzuntar "$images_dir/fuel-images.tar.lrz"
popd &>/dev/null
service docker start

# load docker images
for image in $images_dir/*tar ; do
    echo "Loading docker image ${image}..."
    docker load -i "$image"
done

# clean up extracted images
rm -f $images_dir/*tar

#FIXME(mattymo) Write astute.yaml to /etc/fuel from fuelmenu
cp -a /etc/astute.yaml /etc/fuel/astute.yaml

# apply puppet
puppet apply -d -v /etc/puppet/modules/nailgun/examples/host-only.pp
rmdir /var/log/remote && ln -s /var/log/docker-logs/remote /var/log/remote

echo -n "Waiting for Fuel UI to be ready..."
curl -s --retry 100 --retry-delay 1 "http://127.0.0.1:8000/api/version" -o
/dev/null
if [ $? -ne 0 ]; then
  echo "failed! Check logs for details."
else
  echo "done!"
fi

echo "Fuel node deployment complete!"
