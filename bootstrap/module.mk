/:=$(BUILD_DIR)/bootstrap/
INITRAM_DIR=$/initram-root
INITRAM_FS=$/initramfs.img
LINUX=$/linux

.PHONY: bootstrap clean
all: bootstrap

YUM_PACKAGES=puppet openssh-server wget cronie-noanacron crontabs ntp \
mcollective bash net-tools dhclient rsyslog iputils openssh-server \
ruby-json rubygems mcollective vconfig tcpdump scapy mingetty

YUM_BUILD_PACKAGES=ruby-devel make gcc flex byacc python-devel \
glibc-devel glibc-headers kernel-headers

NAILGUN_DIR=$(INITRAM_DIR)/opt/nailgun

RPM=sudo rpm --root=`readlink -f $(INITRAM_DIR)`
YUM=sudo yum --installroot=`readlink -f $(INITRAM_DIR)` -y --nogpgcheck
RPM_DIR=$(CENTOS_REPO_DIR)Packages
CHROOT_CMD=sudo chroot $(INITRAM_DIR)

clean: clean-bootstrap

clean-bootstrap:
	-sudo umount $(INITRAM_DIR)/proc
	-sudo umount $(INITRAM_DIR)/dev
	sudo rm -rf $(INITRAM_DIR)

%: /:=$/


bootstrap: $(LINUX) $(INITRAM_FS)


$(INITRAM_FS): $(NAILGUN_DIR)
	sudo rm -rf $(INITRAM_DIR)/var/cache/yum $(INITRAM_DIR)/usr/share/doc \
        $(INITRAM_DIR)/usr/share/locale $(INITRAM_DIR)/src $(INITRAM_DIR)/etc/yum.repos.d
	sudo sh -c "cd $(INITRAM_DIR) && find . -xdev | cpio --create \
        --format='newc' | gzip -9 > `readlink -f $(INITRAM_FS)`"


$(LINUX): | $(BUILD_DIR)/packages/centos/cache.done
	mkdir -p $/
	find $(RPM_DIR) -name 'kernel-2.*' | xargs rpm2cpio | cpio -imdv './boot/vmlinuz*'
	mv boot/vmlinuz* $(LINUX)


$(NAILGUN_DIR): | $(INITRAM_DIR)/etc/init $(BUILD_DIR)/packages/centos/cache.done
	find $(RPM_DIR) -name 'kernel-2.*' | xargs rpm2cpio | \
        ( cd $(INITRAM_DIR); sudo cpio -idm './lib/modules/*' './boot/vmlinuz*' )
	find $(RPM_DIR) -name 'kernel-firmware-2.*' | xargs rpm2cpio | \
        ( cd $(INITRAM_DIR); sudo cpio -idm './lib/firmware/*' )
	for version in `ls -1 $(INITRAM_DIR)/lib/modules`; do \
          sudo depmod -b $(INITRAM_DIR) $$version; \
	done
	sudo sed -i -e '/^root/c\root:$$6$$oC7haQNQ$$LtVf6AI.QKn9Jb89r83PtQN9fBqpHT9bAFLzy.YVxTLiFgsoqlPY3awKvbuSgtxYHx4RUcpUqMotp.WZ0Hwoj.:15441:0:99999:7:::' $(INITRAM_DIR)/etc/shadow
	sudo cp -r bootstrap/sync/* $(INITRAM_DIR)
	sudo mkdir -p $(NAILGUN_DIR)/bin
	sudo cp -r bin/agent $(NAILGUN_DIR)/bin
	echo "bootstrap" | sudo tee $(NAILGUN_DIR)/system_type
	sudo mkdir -p $(INITRAM_DIR)/root/.ssh
	sudo cp bootstrap/ssh/id_rsa.pub $(INITRAM_DIR)/root/.ssh/authorized_keys


$(INITRAM_DIR)/etc/init: $(BUILD_DIR)/packages/centos/repo.done $(INITRAM_DIR)/etc/yum.repos.d/mirror.repo | $(INITRAM_DIR)/dev/urandom $(INITRAM_DIR)/proc/1
	sudo mkdir -p $(INITRAM_DIR)/var/lib/rpm
	$(RPM) --rebuilddb
	$(YUM) install $(YUM_PACKAGES) $(YUM_BUILD_PACKAGES)
	sudo cp /etc/resolv.conf $(INITRAM_DIR)/etc/resolv.conf
	$(CHROOT_CMD) gem install --no-rdoc --no-ri httpclient
	$(CHROOT_CMD) gem install --no-rdoc --no-ri ohai
	sudo mkdir -p $(INITRAM_DIR)/src
	cd $(INITRAM_DIR)/src && sudo wget -c http://pypcap.googlecode.com/files/pypcap-1.1.tar.gz \
        http://www.tcpdump.org/release/libpcap-1.3.0.tar.gz
	cd $(INITRAM_DIR)/src && sudo tar zxf libpcap-1.3.0.tar.gz
	cd $(INITRAM_DIR)/src && sudo tar zxf pypcap-1.1.tar.gz
	(cd $(INITRAM_DIR)/src && sudo patch -p1) < bootstrap/pypcap.diff
	$(CHROOT_CMD) /bin/sh -c "cd /src/libpcap-1.3.0 && ./configure && make"
	$(CHROOT_CMD) /bin/sh -c "cd /src/pypcap-1.1 && make && make install"
	$(YUM) erase $(YUM_BUILD_PACKAGES)
	sudo touch $(INITRAM_DIR)/etc/fstab
	sudo rm $(INITRAM_DIR)/etc/resolv.conf
	sudo cp $(INITRAM_DIR)/sbin/init $(INITRAM_DIR)/init
	sudo umount $(INITRAM_DIR)/proc
	sudo umount $(INITRAM_DIR)/dev


define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(shell readlink -f $(BUILD_DIR))/packages/centos/Packages
gpgcheck=0
enabled=1
endef


$(INITRAM_DIR)/etc/yum.repos.d/mirror.repo: export contents:=$(yum_local_repo)
$(INITRAM_DIR)/etc/yum.repos.d/mirror.repo:
	sudo mkdir -p $(@D)
	echo "$${contents}" | sudo tee $@ > /dev/null


$(INITRAM_DIR)/dev/urandom $(INITRAM_DIR)/proc/1:
	sudo mkdir -p $(INITRAM_DIR) $(INITRAM_DIR)/proc $(INITRAM_DIR)/dev
	mount | grep $(INITRAM_DIR)/proc || sudo mount --bind /proc $(INITRAM_DIR)/proc
	mount | grep $(INITRAM_DIR)/dev || sudo mount --bind /dev $(INITRAM_DIR)/dev
