#!/bin/bash
mkdir -p /var/log/puppet
exec > >(tee -i /var/log/puppet/bootstrap_admin_node.log)
exec 2>&1

FUEL_RELEASE=$(grep release: /etc/fuel/version.yaml | cut -d: -f2 | tr -d '" ')

function countdown() {
  local i
  sleep 1
  for ((i=$1-1; i>=1; i--)); do
    printf '\b\b\b\b%04d' "$i"
    sleep 1
  done
}

function fail() {
  echo "ERROR: Fuel node deployment FAILED! Check /var/log/puppet/bootstrap_admin_node.log for details" 1>&2
  exit 1
}

function get_ethernet_interfaces() {
  # Get list of all ethernet interfaces, non-virtual, not a wireless
  for DEV in /sys/class/net/* ; do
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
         # Virtual lo, bound, vlan, tunneling has been skipped before
         if test -d $DEV/wireless -o -L $DEV/phy80211 ;
         then
              continue
         else
         # Catch ethernet non-virtual device
              echo $IF
         fi
         ;;
         *) continue
         ;;
    esac
  done
}

# Get value of a key from ifcfg-* files
# Usage:
#   get_ifcfg_value NAME /etc/sysconfig/network-scripts/ifcfg-eth0
function get_ifcfg_value {
    local key=$1
    local path=$2
    local value=''
    if [[ -f ${path} ]]; then
        value=$(awk -F\= "\$1==\"${key}\" {print \$2}" ${path})
        value=${value//\"/}
    fi
    echo ${value}
}

# Workaround to fix dracut network configuration approach:
#   Bring down all network interfaces which have the same IP
#   address statically configured as 'primary' interface
function ifdown_ethernet_interfaces {
    local adminif_ipaddr
    local if_config
    local if_name
    local if_ipaddr

    adminif_ipaddr=$(get_ifcfg_value IPADDR /etc/sysconfig/network-scripts/ifcfg-${ADMIN_INTERFACE})
    for if_config in $(find /etc/sysconfig/network-scripts -name 'ifcfg-*' ! -name 'ifcfg-lo'); do
        if_name=$(get_ifcfg_value NAME $if_config)
        if [[ "${if_name}" == "${ADMIN_INTERFACE}" ]]; then
            continue
        fi
        if_ipaddr=$(get_ifcfg_value IPADDR $if_config)
        if [[ "${if_ipaddr}" == "${adminif_ipaddr}" ]]; then
            echo "Interface '${if_name}' uses the same ip '${if_ipaddr}' as admin interface '${ADMIN_INTERFACE}', removing ..."
            ifdown ${if_name}
            rm -f ${if_config}
        fi
    done
}

# Check if interface name is valid by checking that
# a config file with NAME equal to given name exists.
function ifname_valid {
    local adminif_name=$1
    local if_name
    local if_config
    for if_config in $(find /etc/sysconfig/network-scripts -name 'ifcfg-*' ! -name 'ifcfg-lo'); do
        if_name=$(get_ifcfg_value NAME $if_config)
        if [[ "${if_name}" == "${adminif_name}" ]]; then
            return 0
        fi
    done
    return 1
}


# LANG variable is a workaround for puppet-3.4.2 bug. See LP#1312758 for details
export LANG=en_US.UTF8
# Be sure, that network devices have been initialized
udevadm trigger --subsystem-match=net
udevadm settle

# Import bootstrap_admin_node.conf if exists
if [ -f /etc/fuel/bootstrap_admin_node.conf ]; then
    source /etc/fuel/bootstrap_admin_node.conf
fi

# Set defaults to unset / empty variables
# Although eth0 is not always valid it's a good well-known default
# If there is no such interface it will fail to pass ifname_valid
# check and will be replaced.
ADMIN_INTERFACE=${ADMIN_INTERFACE:-'eth0'}
showmenu=${showmenu:-'no'}

# Now check that ADMIN_INTERFACE points to a valid interface
# If it doesn't fallback to getting the first interface name
# from a list of all available interfaces sorted alphabetically
if ! ifname_valid $ADMIN_INTERFACE; then
    # Take the very first ethernet interface as an admin interface
    ADMIN_INTERFACE=$(get_ethernet_interfaces | sort -V | head -1)
fi

echo "Applying admin interface '$ADMIN_INTERFACE'"
export ADMIN_INTERFACE

echo "Bringing down ALL network interfaces except '${ADMIN_INTERFACE}'"
ifdown_ethernet_interfaces
systemctl restart network

echo "Disabling offloading on ${ADMIN_INTERFACE}"
ethtool -K ${ADMIN_INTERFACE} gso off gro off tso off

echo "Applying default Fuel settings..."
set -x
fuelmenu --save-only --iface=$ADMIN_INTERFACE
set +x
echo "Done!"

if [[ "$showmenu" == "yes" || "$showmenu" == "YES" ]]; then
  fuelmenu
  else
  #Give user 15 seconds to enter fuelmenu or else continue
  echo
  echo -n "Press a key to enter Fuel Setup (or press ESC to skip)...   15"
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

# Enable sshd
systemctl enable sshd
systemctl start sshd

# Enable iptables
systemctl enable iptables.service
systemctl start iptables.service


if [ "$wait_for_external_config" == "yes" ]; then
  wait_timeout=3000
  pidfile=/var/lock/wait_for_external_config
  echo -n "Waiting for external configuration (or press ESC to skip)...
$wait_timeout"
  countdown $wait_timeout & countdown_pid=$!
  exec -a wait_for_external_config sleep $wait_timeout & wait_pid=$!
  echo $wait_pid > $pidfile
  while ps -p $countdown_pid &> /dev/null && ps -p $wait_pid &>/dev/null; do
    read -s -n 1 -t 2 key
    case "$key" in
      $'\e')   echo -e "\b\b\b\b abort on user input"
               break
               ;;
      *)       ;;
    esac
  done
  { kill $countdown_pid $wait_pid & wait $!; }
  rm -f $pidfile
fi


#Reread /etc/sysconfig/network to inform puppet of changes
. /etc/sysconfig/network
hostname "$HOSTNAME"

# XXX: ssh keys which should be included into the bootstrap image are
# generated during containers deployment. However cobbler checkfs for
# a kernel and initramfs when creating a profile, which poses chicken
# and egg problem. Fortunately cobbler is pretty happy with empty files
# so it's easy to break the loop.
make_ubuntu_bootstrap_stub () {
        local bootstrap_dir='/var/www/nailgun/bootstraps/active_bootstrap'
        local bootstrap_stub_dir='/var/www/nailgun/bootstraps/bootstrap_stub'
        mkdir -p ${bootstrap_stub_dir}
        for item in vmlinuz initrd.img; do
                touch "${bootstrap_stub_dir}/$item"
        done
        ln -s ${bootstrap_stub_dir} ${bootstrap_dir} || true
}

get_bootstrap_flavor () {
	local ASTUTE_YAML='/etc/fuel/astute.yaml'
	python <<-EOF
	from fuelmenu.fuelmenu import Settings
	conf = Settings().read("$ASTUTE_YAML").get('BOOTSTRAP', {})
	print(conf.get('flavor', 'centos').lower())
	EOF
}

get_bootstrap_skip () {
	local ASTUTE_YAML='/etc/fuel/astute.yaml'
	python <<-EOF
	from fuelmenu.fuelmenu import Settings
	conf = Settings().read("$ASTUTE_YAML").get('BOOTSTRAP', {})
	print(conf.get('skip_default_img_build', False))
	EOF
}

# Actually build the bootstrap image
build_ubuntu_bootstrap () {
	local log='/var/log/fuel-bootstrap-image-build.log'
        local ret=1
	echo "Bulding default ubuntu-bootstrap image" >&2
	if fuel-bootstrap -v --debug build --activate --notify-webui >>"$log" 2>&1; then
		ret=0
	fi
        if [ $ret -ne 0 ]; then
		# FIXME Add correct how-to url and problem description
		warning="WARNING: Failed to build the bootstrap image, see $log
for details. Perhaps your Internet connection is broken. Please fix the problem and run
\`fuel-bootstrap build --activate --notify-webui\`"
                fuel notify --topic warning --send "$warning"
        fi
        return $ret
}


# Create empty files to make cobbler happy
# (even if we don't use Ubuntu based bootstrap)
make_ubuntu_bootstrap_stub

service docker start

old_sysctl_vm_value=$(sysctl -n vm.min_free_kbytes)
if [ ${old_sysctl_vm_value} -lt 65535 ]; then
  echo "Set vm.min_free_kbytes..."
  sysctl -w vm.min_free_kbytes=65535
fi

if [ -f /root/.build_images ]; then
  #Fail on all errors
  set -e
  trap fail EXIT

  echo "Loading Fuel base image for Docker..."
  docker load -i /var/www/nailgun/docker/images/fuel-images.tar

  echo "Building Fuel Docker images..."
  WORKDIR=$(mktemp -d /tmp/docker-buildXXX)
  SOURCE=/var/www/nailgun/docker
  REPO_CONT_ID=$(docker -D run -d -p 80 -v /var/www/nailgun:/var/www/nailgun fuel/centos sh -c 'mkdir -p /var/www/html/repo/os;ln -sf /var/www/nailgun/centos/x86_64 /var/www/html/repo/os/x86_64;ln -s /var/www/nailgun/mos-centos/x86_64 /var/www/html/mos-repo;/usr/sbin/apachectl -DFOREGROUND')
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
    sed -r -e 's/^"?PRODUCTION"?:.*/PRODUCTION: "docker-build"/' -i $WORKDIR/$image/etc/fuel/astute.yaml
    # FIXME(kozhukalov): Once this patch https://review.openstack.org/#/c/219581/ is merged
    # remove this line. fuel-library is to use PRODUCTION value from astute.yaml instead of
    # the same value from version.yaml. It is a part of version.yaml deprecation plan.
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

if [ ${old_sysctl_vm_value} -lt 65535 ]; then
  echo "Restore sysctl vm.min_free_kbytes value..."
  sysctl -w vm.min_free_kbytes=${old_sysctl_vm_value}
fi

# apply puppet
puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/host-only.pp
if [ $? -ge 4 ];then
  fail
fi

# Sync time
systemctl stop ntpd
systemctl start ntpdate || echo "Failed to synchronize time with 'ntpdate'"
systemctl start ntpd

rmdir /var/log/remote && ln -s /var/log/docker-logs/remote /var/log/remote

dockerctl check || fail
bash /etc/rc.local

if [ "`get_bootstrap_flavor`" = "ubuntu" ] && [ "`get_bootstrap_skip`" = "False" ]; then
	build_ubuntu_bootstrap || true
fi

# Enable updates repository
cat > /etc/yum.repos.d/mos${FUEL_RELEASE}-updates.repo << EOF
[mos${FUEL_RELEASE}-updates]
name=mos${FUEL_RELEASE}-updates
baseurl=http://mirror.fuel-infra.org/mos-repos/centos/mos${FUEL_RELEASE}-centos\$releasever-fuel/updates/x86_64/
gpgcheck=0
skip_if_unavailable=1
EOF

# Enable security repository
cat > /etc/yum.repos.d/mos${FUEL_RELEASE}-security.repo << EOF
[mos${FUEL_RELEASE}-security]
name=mos${FUEL_RELEASE}-security
baseurl=http://mirror.fuel-infra.org/mos-repos/centos/mos${FUEL_RELEASE}-centos\$releasever-fuel/security/x86_64/
gpgcheck=0
skip_if_unavailable=1
EOF

#Check if repo is accessible
echo "Checking for access to updates repository..."
repourl=$(yum repolist all -v | awk '{if ($1 ~ "baseurl" && $3 ~ "updates") print $3}' | head -1)
if urlaccesscheck check "$repourl" ; then
  UPDATE_ISSUES=0
else
  UPDATE_ISSUES=1
fi

if [ $UPDATE_ISSUES -eq 1 ]; then
  message="There is an issue connecting to the Fuel update repository. \
Please fix your connection prior to applying any updates. \
Once the connection is fixed, we recommend reviewing and applying \
Maintenance Updates for this release of Mirantis OpenStack: \
https://docs.mirantis.com/openstack/fuel/fuel-${FUEL_RELEASE}/\
release-notes.html#maintenance-updates"
  level="warning"
else
  message="We recommend reviewing and applying Maintenance Updates \
for this release of Mirantis OpenStack: \
https://docs.mirantis.com/openstack/fuel/fuel-${FUEL_RELEASE}/\
release-notes.html#maintenance-updates"
  level="done"
fi
echo
echo "*************************************************"
echo -e "${message}"
echo "*************************************************"
echo "Sending notification to Fuel UI..."
fuel notify --topic "${level}" --send $(echo "${message}" | tr '\r\n' ' ')

# TODO(kozhukalov) If building of bootstrap image fails
# and if this image was supposed to be a default bootstrap image
# we need to warn a user about this and give her
# advice how to treat this.

echo "Fuel node deployment complete!"
# Sleep for agetty autologon
sleep 3
