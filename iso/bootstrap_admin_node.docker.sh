#!/bin/bash
FUEL_RELEASE=$(grep release: /etc/fuel/version.yaml | cut -d: -f2 | tr -d '" ')

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
  docker load -i /var/www/nailgun/docker/images/fuel-images.tar

  echo "Building Fuel Docker images..."
  WORKDIR=$(mktemp -d /tmp/docker-buildXXX)
  SOURCE=/var/www/nailgun/docker
  REPO_CONT_ID=$(docker -D run -d -p 80 -v /var/www/nailgun:/var/www/nailgun fuel/centos sh -c 'mkdir /var/www/html/os;ln -sf /var/www/nailgun/centos/x86_64 /var/www/html/os/x86_64;/usr/sbin/apachectl -DFOREGROUND')
  RANDOM_PORT=$(docker port $REPO_CONT_ID 80 | cut -d':' -f2)

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
    docker build -t fuel/${image}_${FUEL_RELEASE} $WORKDIR/$image
  done
  docker rm -f $REPO_CONT_ID
  rm -rf "$WORKDIR"

  #Remove trap for normal deployment
  trap - EXIT
  set +e
else
  echo "Loading docker images. (This may take a while)"
  docker load -i /var/www/nailgun/docker/images/fuel-images.tar
fi

# apply puppet
puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/host-only.pp
if [ $? -ge 4 ];then
  fail
fi
rmdir /var/log/remote && ln -s /var/log/docker-logs/remote /var/log/remote

dockerctl check || fail
bash /etc/rc.local

# Enable updates repository
cat > /etc/yum.repos.d/mos${FUEL_RELEASE}-updates.repo << EOF
[mos${FUEL_RELEASE}-updates]
name=mos${FUEL_RELEASE}-updates
baseurl=http://mirror.fuel-infra.org/mos/centos-6/mos${FUEL_RELEASE}/updates/
gpgcheck=0
skip_if_unavailable=1
EOF

# Enable security repository
cat > /etc/yum.repos.d/mos${FUEL_RELEASE}-security.repo << EOF
[mos${FUEL_RELEASE}-security]
name=mos${FUEL_RELEASE}-security
baseurl=http://mirror.fuel-infra.org/mos/centos-6/mos${FUEL_RELEASE}/security/
gpgcheck=0
skip_if_unavailable=1
EOF

#Check if repo is accessible
echo "Checking for access to updates repository..."
repourl=$(grep baseurl /etc/yum.repos.d/*updates* 2>/dev/null | cut -d'=' -f2- | head -1)
if urlaccesscheck check "$repourl" ; then
  UPDATE_ISSUES=0
else
  UPDATE_ISSUES=1
fi

if [ $UPDATE_ISSUES -eq 1 ]; then
  warning="WARNING: There are issues connecting to Fuel update repository.\
\nPlease fix your connection and update this node with \`yum update\`\
\nThen run \`dockerctl destroy all; bootstrap_admin_node.sh;\`\
\nto repeat bootstrap on Fuel Master with the latest updates.\
\nFor more information, check out Fuel documentation at:\
\nhttp://docs.mirantis.com/fuel"
else
  warning="WARNING: There may be updates available for Fuel.\
\nYou should update this node with \`yum update\`. If there are available\
\n updates, run \`dockerctl destroy all; bootstrap_admin_node.sh;\`\
\nto repeat bootstrap on Fuel Master with the latest updates.\
\nFor more information, check out Fuel documentation at:\
\nhttp://docs.mirantis.com/fuel"
fi
echo
echo "*************************************************"
echo -e "$warning"
echo "*************************************************"
echo "Sending notification to Fuel UI..."
fuel notify --topic warning --send "$warning"
echo "Fuel node deployment complete!"
