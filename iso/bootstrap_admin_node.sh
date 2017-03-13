#!/bin/bash

# LANG variable is a workaround for puppet-3.4.2 bug. See LP#1312758 for details
export LANG=en_US.UTF8

wwwdir="/var/www/nailgun"

mkdir -p /var/log/puppet
mkdir -p ${wwwdir}/targetimages

LOGFILE=${LOGFILE:-/var/log/puppet/bootstrap_admin_node.log}

exec > >(tee -i "${LOGFILE}")
exec 2>&1

# LP#1535419: Hide too verbose kernel messages to prevent tty being
# filled with spam.
sysctl -w kernel.printk='4 1 1 7'

VBOX_BLACKLIST_MODULES="i2c_piix4 intel_rapl"

# The following packages need to be installed prior to installing any other ones
# fuel-release package should be installed at the end of all bootstrap packages
# since it introduces online mirrors which might be unavailable in isolated envs
BOOTSTRAP_PACKAGES="yum-plugin-priorities yum-utils fuel-release"

FUEL_PACKAGES=" \
augeas \
authconfig \
bind-utils \
bridge-utils \
daemonize \
dhcp \
fuel \
fuel-bootstrap-cli \
fuel-openstack-metadata \
fuel-utils \
fuel-ui \
gdisk \
lrzip \
lsof \
mlocate \
nmap-ncat \
ntp \
ntpdate \
puppet \
python-pypcap \
python-timmy \
rsync \
rubygem-netaddr \
rubygem-openstack \
send2syslog \
strace \
sysstat \
system-config-firewall-base \
tcpdump \
telnet \
vim \
virt-what \
wget \
"

ASTUTE_YAML='/etc/fuel/astute.yaml'
BOOTSTRAP_NODE_CONFIG="/etc/fuel/bootstrap_admin_node.conf"
CUSTOM_REPOS="/root/default_deb_repos.yaml"
bs_build_log='/var/log/fuel-bootstrap-image-build.log'
bs_status=0
# Backup network configs to this folder. Folder will be created only if
# backup process actually will be.
bup_folder="/var/bootstrap_admin_node_bup_$(date +%Y-%m-%d-%H-%M-%S)/"
### Long messages inside code makes them more complicated to read...
# bootstrap messages
# FIXME fix help links
bs_skip_message="WARNING: Ubuntu bootstrap build has been skipped. \
Please build and activate bootstrap manually with CLI command \
\`fuel-bootstrap build --activate\`. \
While you don't activate any bootstrap - new nodes cannot be discovered \
and added to cluster. \
For more information please visit \
http://docs.openstack.org/developer/fuel-docs/userdocs/fuel-install-guide/bootstrap/\
bootstrap_troubleshoot.html"
bs_error_message="WARNING: Failed to build the bootstrap image, see $bs_build_log \
for details. Perhaps your Internet connection is broken. Please fix the \
problem and run \`fuel-bootstrap build --activate\`. \
While you don\'t activate any bootstrap - new nodes cannot be discovered \
and added to cluster. \
For more information please visit \
http://docs.openstack.org/developer/fuel-docs/userdocs/fuel-install-guide/bootstrap/\
bootstrap_troubleshoot.html"
bs_progress_message="There is no active bootstrap. Bootstrap image building \
is in progress. Usually it takes 15-20 minutes. It depends on your internet \
connection and hardware performance. After bootstrap image becomes available, \
reboot nodes that failed to be discovered."
bs_done_message="Default bootstrap image building done. Now you can boot new \
nodes over PXE, they will be discovered and become available for installing \
OpenStack on them"
# Update issues messages
update_warn_message="There is an issue connecting to update repository of \
your distributions of OpenStack. \
Please fix your connection prior to applying any updates. \
Once the connection is fixed, we recommend reviewing and applying \
maintenance updates for your distribution of OpenStack."
update_done_message="We recommend reviewing and applying maintenance updates \
for your distribution of OpenStack."
fuelmenu_fail_message="Fuelmenu was not able to generate '/etc/fuel/astute.yaml' file! \
Please, restart it manualy using 'fuelmenu' command."
fuelclient_fail_message="Fuel CLI credentials are invalid. Update \
/etc/fuel/astute.yaml FUEL_ACCESS/password and ~/.config/fuel/fuel_client.yaml\
 in order to proceed with deployment."
function countdown() {
  local i
  sleep 1
  for ((i=$1-1; i>=1; i--)); do
    printf '\b\b\b\b%04d' "$i"
    sleep 1
  done
}

function fail() {
  MSG="ERROR: Fuel node deployment FAILED! Check ${LOGFILE} for details"
  # LP: #1551658 - Ensure data will be flushed on disk
  sed -i -u "\$a${MSG}" "${LOGFILE}"

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

# Get IP address from interface name
function get_interface_ip {
    local interface=$1
    echo $(ip -4 -o a s ${interface} | sed 's:/:\ :;s:\s\+:\ :g' | cut -d ' ' -f 4)
}

# Workaround to fix dracut network configuration approach:
#   Bring down all network interfaces which have the same IP
#   address statically configured as 'primary' interface
function ifdown_ethernet_interfaces {
    local adminif_ipaddr
    local if_name
    local if_ipaddr
    local path

    adminif_ipaddr=$(get_interface_ip $ADMIN_INTERFACE)
    if [[ -z "${adminif_ipaddr}" ]]; then
        return
    fi
    for if_name in $(get_ethernet_interfaces); do
        if [[ "${if_name}" == "${ADMIN_INTERFACE}" ]]; then
            continue
        fi
        if_ipaddr=$(get_interface_ip $if_name)
        if [[ "${if_ipaddr}" == "${adminif_ipaddr}" ]]; then
            echo "Interface '${if_name}' uses the same ip '${if_ipaddr}' as admin interface '${ADMIN_INTERFACE}', removing ..."
            ifdown ${if_name}
            mkdir -p "${bup_folder}"
            path="/etc/sysconfig/network-scripts/ifcfg-${if_name}"
            if [[ -f ${path} ]]; then
                mv -f "${path}" "${bup_folder}"
            fi
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

# switch selinux to permissive mode
setenforce 0
sed -i s/SELINUX=enforcing/SELINUX=permissive/g /etc/selinux/config || :

yum makecache
echo $BOOTSTRAP_PACKAGES | xargs -n1 yum install -y
# /etc/fuel_release is provided by 'fuel-release' package
FUEL_RELEASE=$(cat /etc/fuel_release)

# Disable online base MOS repo if we run an ISO installation
[ -f /etc/fuel_build_id ] && yum-config-manager --disable mos${FUEL_RELEASE}* --save

echo $FUEL_PACKAGES | xargs -n1 yum install -y
# /etc/fuel_openstack_version is provided by 'fuel-openstack-metadata' package
OPENSTACK_VERSION=$(cat /etc/fuel_openstack_version)


touch /var/lib/hiera/common.yaml /etc/puppet/hiera.yaml

# Be sure, that network devices have been initialized
udevadm trigger --subsystem-match=net
udevadm settle

# Import bootstrap_admin_node.conf if exists
if [ -f "${BOOTSTRAP_NODE_CONFIG}" ]; then
    source "${BOOTSTRAP_NODE_CONFIG}"
fi

# Set defaults to unset / empty variables
# Although eth0 is not always valid it's a good well-known default
# If there is no such interface it will fail to pass ifname_valid
# check and will be replaced.
OLD_ADMIN_INTERFACE=${ADMIN_INTERFACE}
ADMIN_INTERFACE=${ADMIN_INTERFACE:-'eth0'}
showmenu=${showmenu:-'yes'}

# Now check that ADMIN_INTERFACE points to a valid interface
# If it doesn't fallback to getting the first interface name
# from a list of all available interfaces sorted alphabetically
if ! ifname_valid $ADMIN_INTERFACE; then
    # Take the very first ethernet interface as an admin interface
    ADMIN_INTERFACE=$(get_ethernet_interfaces | sort -V | head -1)
fi

if [[ "${OLD_ADMIN_INTERFACE}" != "${ADMIN_INTERFACE}" ]]; then
  echo "Saving ADMIN_INTERFACE value"
  sed -i "s/^ADMIN_INTERFACE=.*/ADMIN_INTERFACE=${ADMIN_INTERFACE}/g" \
    ${BOOTSTRAP_NODE_CONFIG}
fi

echo "Applying admin interface '$ADMIN_INTERFACE'"
export ADMIN_INTERFACE

echo "Bringing down ALL network interfaces except '${ADMIN_INTERFACE}'"
ifdown_ethernet_interfaces
systemctl restart network

echo "Applying default Fuel settings..."
set -x

# Disable subscription-manager plugins
sed -i 's/^enabled.*/enabled=0/' /etc/yum/pluginconf.d/product-id.conf || :
sed -i 's/^enabled.*/enabled=0/' /etc/yum/pluginconf.d/subscription-manager.conf || :

# Disable GSSAPI in ssh server config
sed -i -e "/^\s*GSSAPICleanupCredentials yes/d" -e "/^\s*GSSAPIAuthentication yes/d" /etc/ssh/sshd_config

# Enable MOTD banner in sshd
sed -i -e "s/^\s*PrintMotd no/PrintMotd yes/g" /etc/ssh/sshd_config

# Add note regarding local repos creation to MOTD
cat >> /etc/motd << EOF

All environments use online repositories by default.
Use the python-packetary package to create local repositories:

yum install python-packetary
packetary --help

Use python-fuelclient package to modify default repository settings:

yum install python-fuelclient (installed by default)
fuel2 --help

EOF

# Generate Fuel UUID
[ ! -f "/etc/fuel/fuel-uuid" ] && uuidgen > /etc/fuel/fuel-uuid || :

echo "tos orphan 7" >> /etc/ntp.conf && systemctl restart ntpd

# Disabling splash
sed -i --follow-symlinks -e '/^\slinux16/ s/rhgb/debug/' /boot/grub2/grub.cfg

# Copying default bash settings to the root directory
cp -f /etc/skel/.bash* /root/

# Blacklist and try to unload kernel modules that create errors on VirtualBox
if (virt-what | fgrep -q "virtualbox") ; then
  for module in $VBOX_BLACKLIST_MODULES; do
    echo "blacklist ${module}" > /etc/modprobe.d/blacklist-${module}.conf
    rmmod ${module} || :
  done
fi

# change default repo path in fuel-menu before starting any deployment steps
if [ -f "${CUSTOM_REPOS}" ]; then
  fix_default_repos.py fuelmenu --repositories-file "${CUSTOM_REPOS}" || fail
fi

# setup stringify_facts for the puppet
augtool set /files/etc/puppet/puppet.conf/main/stringify_facts false

fuelmenu --save-only --iface=$ADMIN_INTERFACE || fail
set +x
echo "Done!"

if [[ "$showmenu" == "yes" || "$showmenu" == "YES" ]]; then
  fuelmenu || fail
else
  # Give user 15 seconds to enter fuelmenu or else continue
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
              fuelmenu || fail
              ;;
    esac
  fi
fi

# Enable online base MOS repos (security, updates) if we run an ISO installation
[ -f /etc/fuel_build_id ] && \
  yum-config-manager --enable mos${FUEL_RELEASE}-security mos${FUEL_RELEASE}-updates --save

if [ ! -f "${ASTUTE_YAML}" ]; then
  echo ${fuelmenu_fail_message}
  fail
fi

# Replace local repository for building bootstrap with online one
# and create symlink for backward compatibility
# if we run deployment on a pre-provisioned server
if [ ! -f /etc/fuel_build_id ]; then
  sed -i "s|127.0.0.1:8080/ubuntu/x86_64|mirror.fuel-infra.org/mos-repos/ubuntu/${FUEL_RELEASE}|g" "${ASTUTE_YAML}"
  ln -s ${wwwdir}/${OPENSTACK_VERSION}/ubuntu ${wwwdir}/ubuntu
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

# Prepare custom /etc/issue logon banner and script for changing IP in it
# We can have several interface naming schemes applied and several interface
# UI will listen on
ipstr=""
NL=$'\n'
for ip in `ip -o -4 addr show | awk '/e[nt][hopsx]/ { split($4, arr, /\//); print arr[1] }'`; do
  ipstr="${ipstr}https://${ip}:8443${NL}"
done
cat > /etc/issue <<EOF
#########################################
#       Welcome to the Fuel server      #
#########################################
Server is running on \m platform

Fuel UI is available on:
$ipstr
Default administrator login:    root
Default administrator password: r00tme

Default Fuel UI login: admin
Default Fuel UI password: admin

Please change root password on first login.

EOF

#Reread /etc/sysconfig/network to inform puppet of changes
. /etc/sysconfig/network
hostname "$HOSTNAME"

# XXX: ssh keys which should be included into the bootstrap image are
# generated during containers deployment. However cobbler checkfs for
# a kernel and initramfs when creating a profile, which poses chicken
# and egg problem. Fortunately cobbler is pretty happy with empty files
# so it's easy to break the loop.
make_ubuntu_bootstrap_stub () {
        local bootstrap_dir="${wwwdir}/bootstraps/active_bootstrap"
        local bootstrap_stub_dir="${wwwdir}/bootstraps/bootstrap_stub"
        mkdir -p ${bootstrap_stub_dir}
        for item in vmlinuz initrd.img; do
                touch "${bootstrap_stub_dir}/$item"
        done
        ln -s ${bootstrap_stub_dir} ${bootstrap_dir} || true
}

get_bootstrap_flavor () {
	python <<-EOF
	from yaml import safe_load
	with open("$ASTUTE_YAML", 'r') as f:
	    conf = safe_load(f).get('BOOTSTRAP', {})
	print(conf.get('flavor', 'ubuntu').lower())
	EOF
}

get_bootstrap_skip () {
	python <<-EOF
	from yaml import safe_load
	with open("$ASTUTE_YAML", 'r') as f:
	    conf = safe_load(f).get('BOOTSTRAP', {})
	print(conf.get('skip_default_img_build', False))
	EOF
}

set_ui_bootstrap_error () {
        # This notify can't be closed or removed by user.
        # For remove notify - send empty string.
        local message=$1
        python <<-EOF
	from fuel_bootstrap.utils import notifier
	notifier.notify_webui('${message}')
	EOF
}

# Actually build the bootstrap image
build_ubuntu_bootstrap () {
        local ret=1
        echo ${bs_progress_message} >&2
        set_ui_bootstrap_error "${bs_progress_message}" >&2
        if fuel-bootstrap -v --debug build --activate >>"$bs_build_log" 2>&1; then
          ret=0
          fuel notify --topic "done" --send "${bs_done_message}"
        else
          ret=1
          set_ui_bootstrap_error "${bs_error_message}" >&2
        fi
        # perform hard-return from func
        # this part will update input $1 variable
        local  __resultvar=$1
        eval $__resultvar="'${ret}'"
        return $ret
}

# Create empty files to make cobbler happy
# (even if we don't use Ubuntu based bootstrap)
make_ubuntu_bootstrap_stub

old_sysctl_vm_value=$(sysctl -n vm.min_free_kbytes)
if [ ${old_sysctl_vm_value} -lt 65535 ]; then
  echo "Set vm.min_free_kbytes..."
  sysctl -w vm.min_free_kbytes=65535
fi

if [ ${old_sysctl_vm_value} -lt 65535 ]; then
  echo "Restore sysctl vm.min_free_kbytes value..."
  sysctl -w vm.min_free_kbytes=${old_sysctl_vm_value}
fi

# Ensure fuelclient can authenticate
output=$(fuel token 2>&1)
if echo "$output" | grep -q "Unauthorized"; then
  echo $fuelclient_fail_message
  fail
fi

# apply puppet
/etc/puppet/modules/fuel/examples/deploy.sh || fail
# Update default repo path
if [ -f "${CUSTOM_REPOS}" ]; then
  fix_default_repos.py fuel \
    --repositories-file "${CUSTOM_REPOS}" \
    --release-version "${OPENSTACK_VERSION}" || fail
fi

# Sync time
systemctl stop ntpd
systemctl start ntpdate || echo "Failed to synchronize time with 'ntpdate'"
systemctl start ntpd

bash /etc/rc.local

if [ "`get_bootstrap_skip`" = "False" ]; then
  build_ubuntu_bootstrap bs_status || true
else
  fuel notify --topic "warning" --send "${bs_skip_message}"
  bs_status=2
fi

#Check if repo is accessible
echo "Checking for access to updates repository/mirrorlist..."
repourl=$(yum repolist all -v | awk '{if ($1 ~ "baseurl|mirrors" && $3 ~ "updates") print $3}' | head -1)
if urlaccesscheck check "$repourl" ; then
  UPDATE_ISSUES=0
else
  UPDATE_ISSUES=1
fi

if [ $UPDATE_ISSUES -eq 1 ]; then
  message=${update_warn_message}
  level="warning"
else
  message=${update_done_message}
  level="done"
fi
echo
echo "*************************************************"
echo -e "${message}"
echo "*************************************************"
fuel notify --topic "${level}" --send $(echo "${message}" | tr '\r\n' ' ') 2>&1

# Perform bootstrap messaging to stdout
case ${bs_status} in
  1)
  echo -e "${bs_error_message}"
  echo "*************************************************"
  ;;
  2)
  echo -e "${bs_skip_message}"
  echo "*************************************************"
  ;;
esac

echo "Fuel node deployment complete!"
# Sleep for agetty autologon
sleep 3
