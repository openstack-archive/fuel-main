#!/bin/bash

[ X`whoami` = X'root' ] || { echo "You must be root"; exit 1; }

SCRIPT=`readlink -f "$0"`
SCRIPTDIR=`dirname ${SCRIPT}`
REPO=${SCRIPTDIR}/..

INITRD_LOOP=/var/tmp/build_basedir/loop_precise_i386
INITRD=/var/tmp/build_basedir/initrd_precise_i386
[ -z ${MIRROR} ] && MIRROR=http://us.archive.ubuntu.com/ubuntu
SUITE=precise

echo "Mounting initrd as loop directory ..."
umount ${INITRD_LOOP}
mount -o loop ${INITRD} ${INITRD_LOOP}

echo  "Updating modules.dep in order to fix modprobe errors ..."
for version in `ls -1 ${INITRD_LOOP}/lib/modules`; do
    depmod -b ${INITRD_LOOP} $version
done

echo "Configuring /etc/network/interfaces ..."
cat > ${INITRD_LOOP}/etc/network/interfaces <<EOF
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
EOF

echo "Configuring /etc/network/interfaces ..."
cat > ${INITRD_LOOP}/etc/hostname <<EOF
bootstrap
EOF

echo "Setting default password for root into r00tme ..." 
sed -i -e '/^root/c\root:$6$oC7haQNQ$LtVf6AI.QKn9Jb89r83PtQN9fBqpHT9bAFLzy.YVxTLiFgsoqlPY3awKvbuSgtxYHx4RUcpUqMotp.WZ0Hwoj.:15441:0:99999:7:::' ${INITRD_LOOP}/etc/shadow


echo "Adding root autologin on tty1 ..."
cat > ${INITRD_LOOP}/usr/bin/autologin <<EOF
#!/bin/sh
/bin/login -f root
EOF
chmod +x ${INITRD_LOOP}/usr/bin/autologin
sed -i -e '/exec/c\exec /sbin/getty -8 -l /usr/bin/autologin 38400 tty1' ${INITRD_LOOP}/etc/init/tty1.conf


echo "Updating sources.list and injecting opscode apt repo ..."
cat > ${INITRD_LOOP}/etc/apt/sources.list <<EOF
deb ${MIRROR} ${SUITE} main
deb ${MIRROR} ${SUITE} universe
deb ${MIRROR} ${SUITE} multiverse
deb ${MIRROR} ${SUITE} restricted
deb http://apt.opscode.com/ ${SUITE}-0.10 main
EOF

echo "Injecting opscode apt repo key ..."
wget --quiet -O - http://apt.opscode.com/packages@opscode.com.gpg.key > ${INITRD_LOOP}/root/opscode.key
chroot ${INITRD_LOOP} /bin/bash <<EOF
cat /root/opscode.key | apt-key add -
EOF

echo "Updating list of available packages ..."
chroot ${INITRD_LOOP} /bin/bash <<EOF
apt-get update
EOF

echo "Preconfiguring chef package (debconf) ..."
chroot ${INITRD_LOOP} /bin/bash <<EOF
echo "chef chef/chef_server_url string http://localhost:4000" | debconf-set-selections
EOF

# FIXME 
# It is necessary to use lxc to configure initrd

echo "Installing chef and disabling it ..."
chroot ${INITRD_LOOP} /bin/bash <<EOF
apt-get -y install chef
update-rc.d chef-client disable
EOF


echo "Injecting cookbooks and configs for chef-solo ..."
cp -r ../cookbooks ${INITRD_LOOP}/root
cp -r ../scripts ${INITRD_LOOP}/root

echo "Injecting crontab job to launch chef-solo ..."
cat > ${INITRD_LOOP}/etc/cron.d/chef-solo <<EOF
*/5 * * * * root flock -w 0 /var/lock/chef-solo.lock /usr/bin/chef-solo -l debug -c /root/scripts/solo.rb -j /root/scripts/solo.json
EOF

echo "Injecting bootstrap ssh key ..."
mkdir -p ${INITRD_LOOP}/root/.ssh
cp ${REPO}/bootstrap/ssh/id_rsa.pub ${INITRD_LOOP}/root/.ssh/authorized_keys 



 


