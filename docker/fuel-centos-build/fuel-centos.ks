install
url --url=http://127.0.0.1/os/x86_64/
lang en_US.UTF-8
keyboard uk
network --device eth0 --bootproto dhcp
rootpw --iscrypted $1$UKLtvLuY$kka6S665oCFmU7ivSDZzU.
authconfig --enableshadow --passalgo=sha512 --enablefingerprint
selinux --disabled
timezone --utc Etc/UTC
#repo --name="CentOS" --baseurl=http://mirror.centos.org/centos/6/os/x86_64/ --cost=100
repo --name="Fuel CentOS" --baseurl=http://127.0.0.1/os/x86_64/ --cost 100
#repo --name="Updates" --baseurl=http://mirror.centos.org/centos-6/6/updates/x86_64/ --cost=100
# CentOSPlus is here ONLY for a libselinux patch.
# Once 6.6 is released, this should be removed
# http://lists.centos.org/pipermail/centos-devel/2014-May/010345.html
#repo --name="CentOSPlus" --baseurl=http://mirror.centos.org/centos-6/6/centosplus/x86_64/ --cost=1000

clearpart --all --initlabel
part / --fstype ext4 --size=2048 --grow
reboot
%packages  --excludedocs --nobase
@Core
-MAKEDEV
-aic94xx-firmware
-atmel-firmware
-b43-openfwwf
-bfa-firmware
-dhclient
-efibootmgr
-ethtool
-initscripts
-iproute
-iptables
-iptables-ipv6
-iputils
-ipw2100-firmware
-ipw2200-firmware
-ivtv-firmware
-iwl100-firmware
-iwl1000-firmware
-iwl3945-firmware
-iwl4965-firmware
-iwl5000-firmware
-iwl5150-firmware
-iwl6000-firmware
-iwl6000g2a-firmware
-iwl6050-firmware
-kbd
-kernel-firmware
-libertas-usb8388-firmware
-openssh-server
-postfix
-policycoreutils
-ql2100-firmware
-ql2200-firmware
-ql23xx-firmware
-ql2400-firmware
-ql2500-firmware
-redhat-logos
-rt61pci-firmware
-rt73usb-firmware
-selinux-policy
-selinux-policy-targeted
-upstart
-xorg-x11-drv-ati-firmware
-zd1211-firmware
cronie-anacron
bzip2
cobbler
cobbler-web
cronie
crontabs
dnsmasq
fence-agents-all
fuel-library
httpd
logrotate
nginx
openstack-keystone
openssh-clients
postgresql-server
postgresql-libs
postgresql
python-alembic
python-amqplib
python-anyjson
python-babel
python-ceilometerclient
python-cinderclient
python-crypto
python-decorator
python-django
python-fabric
python-fysom
python-heatclient
python-iso8601
python-jinja2
python-jsonschema
python-keystoneclient
python-keystonemiddleware
python-kombu
python-mako
python-markupsafe
python-muranoclient
python-netaddr
python-neutronclient
python-netifaces
python-novaclient
python-oslo-config
python-paste
python-ply
python-psycopg2
python-requests
python-saharaclient
python-simplejson
python-six
python-sqlalchemy
python-stevedore
python-urllib3
python-webpy
python-wsgilog
python-wsgiref
PyYAML
python-novaclient
python-networkx-core
pytz
rabbitmq-server
rsync
mcollective
puppet
rubygem-activesupport
rubygem-amqp
rubygem-mcollective-client
rubygem-symboltable
rubygem-rest-client
rubygem-popen4
rubygem-raemon
rubygem-net-ssh
rubygem-net-ssh-gateway
rubygem-net-ssh-multi
screen
send2syslog
sudo
supervisor
sysstat
tar
tftp-server
vim-minimal
xinetd
yum-plugin-priorities
%end

%post
# randomize root password and lock root account
dd if=/dev/urandom count=50 | md5sum | passwd --stdin root
passwd -l root

# create necessary devices
/sbin/MAKEDEV /dev/console

# cleanup unwanted stuff

# ami-creator requires grub during the install, so we remove it (and
# its dependencies) in %post
rpm -e grub redhat-logos
rm -rf /boot

# some packages get installed even though we ask for them not to be,
# and they don't have any external dependencies that should make
# anaconda install them
rpm -e MAKEDEV ethtool upstart initscripts iputils policycoreutils iptables \
    iproute

# Remove files that are known to take up lots of space but leave
# directories intact since those may be required by new rpms.


# locales
# nuking the locales breaks things. Lets not do that anymore
# strip most of the languages from the archive.
localedef --delete-from-archive $(localedef --list-archive | \
grep -v -i ^en | xargs )
# prep the archive template
mv /usr/lib/locale/locale-archive  /usr/lib/locale/locale-archive.tmpl
# rebuild archive
/usr/sbin/build-locale-archive
#empty the template
:>/usr/lib/locale/locale-archive.tmpl


#  man pages and documentation
find /usr/share/{man,doc,info,gnome/help} \
        -type f | xargs /bin/rm


#  cracklib
#find /usr/share/cracklib \
#        -type f | xargs /bin/rm


#  sln
rm -f /sbin/sln


#  ldconfig
rm -rf /etc/ld.so.cache
rm -rf /var/cache/ldconfig/*
rm -rf /var/cache/yum/*

# Suppress hiera warnings
mkdir -p /etc/puppet /var/lib/fuel/ibp
touch /etc/puppet/hiera.yaml /var/lib/hiera/common.yaml

sed -i '/requiretty/s/^/#/g' /etc/sudoers

cat > /usr/bin/service-systemctl-wrapper << 'EOF'
#!/bin/bash

WRAPPER=$(basename ${0})
SUPERVISORD_CONF=/etc/supervisord.conf
declare -A ACTIONS
ACTIONS['service']='start|stop|reload|restart|status'
ACTIONS['systemctl']='is-active|is-enabled|start|stop|reload|restart|status'

functon usage() {
    case ${WRAPPER} in
        'service')
            usage_service
        ;;
        'systemctl')
            usage_systemctl
        ;;
        *)
            echo "Unknown wrapper command '${WRAPPER}'"
        ;;
    esac
}

function usage_systemctl() {
    echo "* Usage: ${WRAPPER} ${ACTIONS[${WRAPPER}]} service_name"
}

function usage_service() {
    echo "* Usage: ${WRAPPER} service_name ${ACTIONS[${WRAPPER}]}"
}

# Get an option from an INI file
# iniget config-file section option
function iniget() {
    local file=$1
    local section=$2
    local option=$3
    local line
    line=$(sed -ne "/^\[$section\]/,/^\[.*\]/ { /^$option[ \t]*=/ p; }" "$file")
    echo ${line#*=}
}


if [ $# -lt 2 ]; then
    usage
    exit 1
fi

case $(basename ${0}) in
    'service')
        service_name=$1
        action=$2
    ;;
    'systemctl')
        action=$1
        service_name=$2
    ;;
esac

if [[ ! "|${ACTIONS[${WRAPPER}]}|" =~ \|${action}\| ]]; then
    echo "Invalid action '${action}'"
    usage
    exit 1
fi

res=0
if [ "${service_name}" == 'supervisord' ]; then
  case ${action} in
    'is-active')
      /etc/init.d/supervisord status || res=$?
    ;;
    'is-enabled')
    ;;
    *)
      /etc/init.d/supervisord ${action} || res=$?
    ;;
  esac
  exit $res
fi

case ${action} in
  'is-active')
    supervisorctl status $service_name || res=$?
  ;;
  'is-enabled')
    value=$(iniget "${SUPERVISORD_CONF}" "program:${service_name}" "autostart")
    [[ "${value}" =~ [Tt]rue ]] || res=1
  ;;
  *)
    supervisorctl $action $service_name || res=$?
  ;;
esac
exit $res
EOF
chmod +x /usr/bin/service-systemctl-wrapper

mv /usr/sbin/service /usr/sbin/service.orig
mv /usr/bin/systemctl /usr/bin/systemctl.orig
ln -nsf /usr/bin/service-systemctl-wrapper /usr/bin/systemctl
ln -nsf /usr/bin/service-systemctl-wrapper /usr/sbin/service

sed -i 's|^nodaemon.*|nodaemon=true|g' /etc/supervisord.conf
sed -i 's|^files.*|files = /etc/supervisord.d/*|g' /etc/supervisord.conf

%end
