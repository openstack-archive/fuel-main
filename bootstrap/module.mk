BS_DIR:=$(BUILD_DIR)/bootstrap
INITRAM_DIR:=$(BS_DIR)/initram-root
INITRAM_FS:=$(BS_DIR)/initramfs.img
LINUX:=$(BS_DIR)/linux

/:=$(BS_DIR)/
$/%: /:=$/

.PHONY: bootstrap clean chroot-bootstrap
all: bootstrap

YUM_PACKAGES:=openssh-server wget cronie-noanacron crontabs ntp \
bash net-tools dhclient rsyslog iputils openssh-clients vim-minimal\
rubygems mcollective vconfig tcpdump scapy mingetty

YUM_BUILD_PACKAGES:=ruby-devel make gcc flex byacc python-devel \
glibc-devel glibc-headers kernel-headers

NAILGUN_DIR:=$(INITRAM_DIR)/opt/nailgun

RPM:=sudo rpm --root=`readlink -f $(INITRAM_DIR)`
YUM:=sudo yum --installroot=`readlink -f $(INITRAM_DIR)` -y --nogpgcheck
RPM_DIR:=$(CENTOS_REPO_DIR)
CHROOT_CMD:=sudo chroot $(INITRAM_DIR)

clean: clean-bootstrap

clean-bootstrap:
	sudo rm -rf $(INITRAM_DIR)

bootstrap: $(LINUX) $(INITRAM_FS)

$/bootstrap.done: $(LINUX) $(INITRAM_FS)
	$(ACTION.TOUCH)

chroot-bootstrap: $(INITRAM_DIR)/etc/nailgun_systemtype $(BS_DIR)/init.done
	sudo mkdir -p $(INITRAM_DIR)/proc $(INITRAM_DIR)/dev
	mount | grep $(INITRAM_DIR)/proc || sudo mount --bind /proc $(INITRAM_DIR)/proc
	mount | grep $(INITRAM_DIR)/dev || sudo mount --bind /dev $(INITRAM_DIR)/dev
	-$(CHROOT_CMD) /bin/bash
	sudo umount $(INITRAM_DIR)/proc
	sudo umount $(INITRAM_DIR)/dev

$(INITRAM_FS): $(INITRAM_DIR)/etc/nailgun_systemtype
	sudo rm -rf $(INITRAM_DIR)/var/cache/yum $(INITRAM_DIR)/var/lib/yum $(INITRAM_DIR)/usr/share/doc \
        $(INITRAM_DIR)/usr/share/locale $(INITRAM_DIR)/src
	sudo sh -c "cd $(INITRAM_DIR) && find . -xdev | cpio --create \
        --format='newc' | gzip -9 > `readlink -f $(INITRAM_FS)`"


$(LINUX): $(LOCAL_MIRROR)/cache.done
	mkdir -p $(BS_DIR)
	find $(RPM_DIR) -name 'kernel-2.*' | xargs rpm2cpio | (cd $(BS_DIR)/; cpio -imd './boot/vmlinuz*')
	mv $(BS_DIR)/boot/vmlinuz* $(LINUX)
	rmdir $(BS_DIR)/boot
	touch $(LINUX)


$(INITRAM_DIR)/etc/nailgun_systemtype: $(BS_DIR)/init.done
	sudo sed -i -e '/^root/c\root:$$6$$oC7haQNQ$$LtVf6AI.QKn9Jb89r83PtQN9fBqpHT9bAFLzy.YVxTLiFgsoqlPY3awKvbuSgtxYHx4RUcpUqMotp.WZ0Hwoj.:15441:0:99999:7:::' $(INITRAM_DIR)/etc/shadow
	sudo cp -r bootstrap/sync/* $(INITRAM_DIR)
	sudo mkdir -p $(INITRAM_DIR)/root/.ssh
	sudo cp bootstrap/ssh/id_rsa.pub $(INITRAM_DIR)/root/.ssh/authorized_keys
	sudo chmod 700 $(INITRAM_DIR)/root/.ssh
	sudo chmod 600 $(INITRAM_DIR)/root/.ssh/authorized_keys
	sudo mkdir -p $(NAILGUN_DIR)/bin
	sudo cp -r bin/agent $(NAILGUN_DIR)/bin
	sudo mkdir -p $(INITRAM_DIR)/usr/libexec/mcollective/mcollective/agent/
	sudo cp mcagent/* $(INITRAM_DIR)/usr/libexec/mcollective/mcollective/agent/
	sudo sh -c "echo bootstrap > $(INITRAM_DIR)/etc/nailgun_systemtype"

$(BS_DIR)/init.done: $(LOCAL_MIRROR)/repo.done $(INITRAM_DIR)/etc/yum.repos.d/mirror.repo
	mkdir -p $(INITRAM_DIR)/var/lib/rpm
	$(RPM) --rebuilddb
	$(YUM) install $(YUM_PACKAGES) $(YUM_BUILD_PACKAGES)
	sudo touch $(INITRAM_DIR)/etc/fstab

	find $(RPM_DIR) -name 'kernel-2.*' | xargs rpm2cpio | \
        ( cd $(INITRAM_DIR); sudo cpio -idm './lib/modules/*' './boot/vmlinuz*' )
	find $(RPM_DIR) -name 'kernel-firmware-2.*' | xargs rpm2cpio | \
        ( cd $(INITRAM_DIR); sudo cpio -idm './lib/firmware/*' )
	for version in `ls -1 $(INITRAM_DIR)/lib/modules`; do \
          sudo depmod -b $(INITRAM_DIR) $$version; \
	done

	sudo cp /etc/resolv.conf $(INITRAM_DIR)/etc/resolv.conf
	$(CHROOT_CMD) gem install --no-rdoc --no-ri httpclient
	$(CHROOT_CMD) gem install --no-rdoc --no-ri ohai
	$(CHROOT_CMD) gem install --no-rdoc --no-ri json
	sudo rm $(INITRAM_DIR)/etc/resolv.conf

	sudo mkdir -p $(INITRAM_DIR)/src
	cd $(INITRAM_DIR)/src && sudo wget -c http://pypcap.googlecode.com/files/pypcap-1.1.tar.gz \
        http://www.tcpdump.org/release/libpcap-1.3.0.tar.gz
	cd $(INITRAM_DIR)/src && sudo tar zxf libpcap-1.3.0.tar.gz
	cd $(INITRAM_DIR)/src && sudo tar zxf pypcap-1.1.tar.gz
	(cd $(INITRAM_DIR)/src && sudo patch -p1) < bootstrap/pypcap.diff
	$(CHROOT_CMD) /bin/sh -c "cd /src/libpcap-1.3.0 && ./configure && make"
	$(CHROOT_CMD) /bin/sh -c "cd /src/pypcap-1.1 && make && make install"
	$(YUM) erase $(YUM_BUILD_PACKAGES)
	rm -f $(INITRAM_DIR)/etc/yum.repos.d/Cent*
	sudo cp $(INITRAM_DIR)/sbin/init $(INITRAM_DIR)/init
	$(ACTION.TOUCH)

define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(shell readlink -f -m $(RPM_DIR))/Packages
gpgcheck=0
enabled=1
endef

$(INITRAM_DIR)/etc/yum.repos.d/mirror.repo: export contents:=$(yum_local_repo)
$(INITRAM_DIR)/etc/yum.repos.d/mirror.repo:
	mkdir -p $(@D)
	sh -c "echo \"$${contents}\" > $@"
