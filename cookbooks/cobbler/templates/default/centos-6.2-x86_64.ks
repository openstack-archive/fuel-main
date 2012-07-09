install
url --url http://<%= node.cobbler.repoaddr %>/centos/6.2
#url --url http://<%= node.cobbler.repoaddr %>/cblr/ks_mirror/centos-6.2-x86_64
#repo --name=base --baseurl=http://<%= node.cobbler.repoaddr %>/centos/6.2
lang en_US.UTF-8
keyboard us

network --onboot yes --device eth0 --bootproto=dhcp
firewall --disable

rootpw  --iscrypted $6$6PKP1tMCaSx8lAkP$3I2iODktkcLGqN1U2C4kC5mPuQy8gXhWjk7DxlS1fhOaI5rNsJGy4kOv0cetgS0nEfMsjAR6shDGD/47d/B0v/
authconfig --enableshadow --passalgo=sha512
selinux --disabled
timezone --utc America/New_York

bootloader --location=mbr --driveorder=sda,hda --append=" rhgb crashkernel=auto"

# Partitioning
clearpart --all
autopart
part swap --recommended
part /boot --fstype=ext2 --size=1024
part / --size=4096 --fstype ext4 --grow

%packages --nobase 
@core
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
openssh-server

%post
# configure yum
rm /etc/yum.repos.d/*
cat > /etc/yum.repos.d/nailgun.repo <<EOF
[nailgun]
name=Nailgun Repository
baseurl=http://<%= node.cobbler.repoaddr %>/centos/6.2
enabled=1
gpgcheck=0
EOF

# configure ssh key
mkdir -p /root/.ssh
chown -R root:root /root/.ssh
chmod 700 /root/.ssh
<%= @late_authorized_keys.init.late_file("/root/.ssh/authorized_keys", "644") %>

# deploy script
mkdir -p /opt/nailgun/bin
<%= @late_deploy.init.late_file("/opt/nailgun/bin/deploy", "755") %>