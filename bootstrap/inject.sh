#!/bin/bash

[ X`whoami` = X'root' ] || { echo "You must be root"; exit 1; }


INITRD_LOOP=/var/tmp/build_basedir/loop_precise_i386
INITRD=/var/tmp/build_basedir/initrd_precise_i386
MIRROR=http://us.archive.ubuntu.com/ubuntu
SUITE=precise

umount ${INITRD_LOOP}
mount -o loop ${INITRD} ${INITRD_LOOP}



# /etc/network/interfaces
cat > ${INITRD_LOOP}/etc/network/interfaces <<EOF
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
EOF

# default password for root is r00tme 
sed -ie '/^root/c\root:$6$oC7haQNQ$LtVf6AI.QKn9Jb89r83PtQN9fBqpHT9bAFLzy.YVxTLiFgsoqlPY3awKvbuSgtxYHx4RUcpUqMotp.WZ0Hwoj.:15441:0:99999:7:::' ${INITRD_LOOP}/etc/shadow


# root autologin tty1
cat > ${INITRD_LOOP}/usr/bin/autologin <<EOF
#!/bin/sh
/bin/login -f root
EOF
chmod +x ${INITRD_LOOP}/usr/bin/autologin
sed -ie '/exec/c\exec /sbin/getty -8 -l /usr/bin/autologin 38400 tty1' ${INITRD_LOOP}/etc/init/tty1.conf

# sources.list
cat > ${INITRD_LOOP}/etc/apt/sources.list <<EOF
deb ${MIRROR} ${SUITE} main
deb ${MIRROR} ${SUITE} universe
deb ${MIRROR} ${SUITE} multiverse
deb ${MIRROR} ${SUITE} restricted
deb http://apt.opscode.com/ ${SUITE}-0.10 main
EOF

wget --quiet -O - http://apt.opscode.com/packages@opscode.com.gpg.key > ${INITRD_LOOP}/root/opscode.key

chroot ${INITRD_LOOP} /bin/bash <<EOF
cat /root/opscode.key | apt-key add -
apt-get update
apt-get -y install chef
EOF








 


