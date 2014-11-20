#!/bin/bash

function countdown() {
  local i
  sleep 1
  for ((i=$1-1; i>=1; i--)); do
    printf '\b\b%02d' "$i"
    sleep 1
  done
}

function fail() {
  echo "ERROR: Fuel node deployment FAILED! Check /var/log/puppet/bootstrap_admin_node.log for details" 1>&2
  exit 1
}
# LANG variable is a workaround for puppet-3.4.2 bug. See LP#1312758 for details
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

service docker start

if [ -f /root/.build_images ]; then
  #Fail on all errors
  set -e
  trap fail EXIT

  echo "Loading Fuel base image for Docker..."
  docker load -i /var/www/nailgun/docker/images/fuel-centos.tar.xz
  docker load -i /var/www/nailgun/docker/images/busybox.tar.xz

  echo "Building Fuel Docker images..."
  RANDOM_PORT=$(shuf -i 9000-65000 -n 1)
  WORKDIR=$(mktemp -d /tmp/docker-buildXXX)
  SOURCE=/var/www/nailgun/docker
  REPODIR="$WORKDIR/repo"
  mkdir -p $REPODIR/os
  ln -s /var/www/nailgun/centos/x86_64 $REPODIR/os/x86_64
  (cd $REPODIR && /var/www/nailgun/docker/utils/simple_http_daemon.py ${RANDOM_PORT} /tmp/simple_http_daemon_${RANDOM_PORT}.pid 5000)
  for imagesource in /var/www/nailgun/docker/sources/*; do
    if ! [ -f "$imagesource/Dockerfile" ]; then
      echo "Skipping ${imagesource}..."
      continue
    fi
    image=$(basename "$imagesource")
    cp -R "$imagesource" $WORKDIR/$image
    mkdir -p $WORKDIR/$image/etc
    cp -R /etc/puppet /etc/fuel $WORKDIR/$image/etc
    sed -e "s/_PORT_/${RANDOM_PORT}/" -i $WORKDIR/$image/Dockerfile
    sed -e 's/production:.*/production: "docker-build"/' -i $WORKDIR/$image/etc/fuel/version.yaml
    docker build -t fuel/${image}_6.0 $WORKDIR/$image
  done
  kill `cat /tmp/simple_http_daemon_${RANDOM_PORT}.pid`
  rm -rf "$WORKDIR"

  #Remove trap for normal deployment
  trap - EXIT
  set +e
else
  images_dir="/var/www/nailgun/docker/images"

  # extract docker images
  mkdir -p $images_dir $sources_dir
  rm -f $images_dir/*tar
  pushd $images_dir &>/dev/null

  echo "Extracting and loading docker images. (This may take a while)"
  lrzip -d -o fuel-images.tar fuel-images.tar.lrz && tar -xf fuel-images.tar && rm -f fuel-images.tar
  popd &>/dev/null

  # load docker images
  for image in $images_dir/*tar ; do
      echo "Loading docker image ${image}..."
      docker load -i "$image"
      # clean up extracted image
      rm -f "$image"
  done
fi

# apply puppet
puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/host-only.pp
if [ $? -ge 4 ];then
  fail
fi
rmdir /var/log/remote && ln -s /var/log/docker-logs/remote /var/log/remote

dockerctl check || fail
bash /etc/rc.local
echo "Fuel node deployment complete!"
