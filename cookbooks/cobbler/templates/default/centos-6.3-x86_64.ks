install
url --url http://<%= node.cobbler.repoaddr %>/centos/6.3
lang en_US.UTF-8
keyboard us
reboot

network --onboot yes --device eth0 --bootproto=dhcp
firewall --disable

rootpw  --iscrypted $6$6PKP1tMCaSx8lAkP$3I2iODktkcLGqN1U2C4kC5mPuQy8gXhWjk7DxlS1fhOaI5rNsJGy4kOv0cetgS0nEfMsjAR6shDGD/47d/B0v/
authconfig --enableshadow --passalgo=sha512
selinux --disabled
timezone --utc America/New_York

bootloader --location=mbr --driveorder=sda,hda --append=" rhgb crashkernel=auto"

# Partitioning
zerombr
clearpart --all --initlabel
autopart
part swap --recommended
part /boot --fstype=ext2 --size=1024
part / --size=4096 --fstype ext4 --grow

%packages --nobase --ignoremissing 
@Core
yum
openssh-server
openssh
openssh-clients
ruby
ruby-devel
ruby-ri
ruby-rdoc
ruby-shadow
gcc
gcc-c++
automake
autoconf
make
curl
dmidecode
rubygems
wget
crontabs
cronie

%post --log=/root/post-install.log
# configure yum
rm /etc/yum.repos.d/*
cat > /etc/yum.repos.d/nailgun.repo <<EOF
[nailgun]
name=Nailgun Repository
baseurl=http://<%= node.cobbler.repoaddr %>/centos/6.3
enabled=1
gpgcheck=0
EOF


# configure ssh key
mkdir -p /root/.ssh
chown -R root:root /root/.ssh
chmod 700 /root/.ssh
<%= @late_authorized_keys.init.cobbler_late_file("/root/.ssh/authorized_keys", "644") %>

# deploy script
mkdir -p /opt/nailgun/bin
<%= @late_deploy.init.cobbler_late_file("/opt/nailgun/bin/deploy", "755") %>

# agent script
mkdir -p /opt/nailgun/bin
<%= @late_agent.init.cobbler_late_file("/opt/nailgun/bin/agent", "755") %>
<%= @late_agent_config.init.cobbler_late_file("/opt/nailgun/bin/agent_config.rb", "644") %>

# rc.local script
<%= @late_rclocal.init.cobbler_late_file("/etc/rc.local", "777") %>

# cron script
mkdir /etc/cron.d
<%= @late_cron.init.cobbler_late_file("/etc/cron.d/agent", "444") %>

# install chef
# gem sources -l | grep -v "*** CURRENT SOURCES ***\|^$" | while read repo; do gem sources -r \${repo}; done
# gem sources -a http://<%= node.cobbler.repoaddr %>/gems/gems
gem install ohai --source http://<%= node.cobbler.repoaddr %>/gems/ --no-ri --no-rdoc
gem install chef --source http://<%= node.cobbler.repoaddr %>/gems/ --no-ri --no-rdoc
gem install httpclient --source http://<%= node.cobbler.repoaddr %>/gems/ --no-ri --no-rdoc

%post --log=/root/nopxe.log
# nopxe
$SNIPPET('disable_pxe')

