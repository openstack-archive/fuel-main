.PHONY: bootstrap clean
all: bootstrap

YUM_PACKAGES:=openssh-server wget cronie-noanacron crontabs ntp \
bash net-tools dhclient rsyslog iputils openssh-clients vim-minimal\
rubygems mcollective vconfig tcpdump scapy mingetty ntp nailgun-net-check dmidecode

YUM_BUILD_PACKAGES:=ruby-devel.x86_64 make gcc flex byacc

NAILGUN_DIR:=$(BUILD_DIR)/bootstrap/initram-root/opt/nailgun

RPM:=sudo rpm --root=`readlink -f $(BUILD_DIR)/bootstrap/initram-root`
YUM:=sudo yum --installroot=`readlink -f $(BUILD_DIR)/bootstrap/initram-root` -y --nogpgcheck
RPM_DIR:=$(CENTOS_REPO_DIR)
CHROOT_CMD:=sudo chroot $(BUILD_DIR)/bootstrap/initram-root

clean: clean-bootstrap

clean-bootstrap:
	sudo rm -rf $(BUILD_DIR)/bootstrap/initram-root

bootstrap: $(BUILD_DIR)/bootstrap/bootstrap.done

$(BUILD_DIR)/bootstrap/bootstrap.done: \
		$(BUILD_DIR)/bootstrap/linux \
		$(BUILD_DIR)/bootstrap/initramfs.img
	$(ACTION.TOUCH)

$(BUILD_DIR)/bootstrap/initramfs.img: $(BUILD_DIR)/bootstrap/initram-root/etc/nailgun_systemtype
	sudo cp -f $(BUILD_DIR)/bootstrap/initram-root/etc/skel/.bash* $(BUILD_DIR)/bootstrap/initram-root/root/
	sudo rm -rf $(BUILD_DIR)/bootstrap/initram-root/var/cache/yum $(BUILD_DIR)/bootstrap/initram-root/var/lib/yum $(BUILD_DIR)/bootstrap/initram-root/usr/share/doc \
        $(BUILD_DIR)/bootstrap/initram-root/usr/share/locale $(BUILD_DIR)/bootstrap/initram-root/src
	sudo sh -c "cd $(BUILD_DIR)/bootstrap/initram-root && find . -xdev | cpio --create \
        --format='newc' | gzip -9 > `readlink -f $(BUILD_DIR)/bootstrap/initramfs.img`"

$(BUILD_DIR)/bootstrap/linux: $(BUILD_DIR)/mirror/build.done
	mkdir -p $(BUILD_DIR)/bootstrap
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'kernel-2.*' | xargs rpm2cpio | (cd $(BUILD_DIR)/bootstrap/; cpio -imd './boot/vmlinuz*')
	mv $(BUILD_DIR)/bootstrap/boot/vmlinuz* $(BUILD_DIR)/bootstrap/linux
	rmdir $(BUILD_DIR)/bootstrap/boot
	touch $(BUILD_DIR)/bootstrap/linux


$(BUILD_DIR)/bootstrap/initram-root/etc/nailgun_systemtype: \
		$(BUILD_DIR)/bootstrap/init.done \
		$(call find-files,bootstrap/sync) \
		$(SOURCE_DIR)/bin/agent \
		$(SOURCE_DIR)/bin/send2syslog.py \
		$(SOURCE_DIR)/bootstrap/ssh/id_rsa.pub \
		$(call find-files,$(SOURCE_DIR)/mcagent)
	sudo sed -i -e '/^root/c\root:$$6$$oC7haQNQ$$LtVf6AI.QKn9Jb89r83PtQN9fBqpHT9bAFLzy.YVxTLiFgsoqlPY3awKvbuSgtxYHx4RUcpUqMotp.WZ0Hwoj.:15441:0:99999:7:::' $(BUILD_DIR)/bootstrap/initram-root/etc/shadow
	sudo cp -r bootstrap/sync/* $(BUILD_DIR)/bootstrap/initram-root
	sudo cp -r bin/send2syslog.py $(BUILD_DIR)/bootstrap/initram-root/usr/bin
	sudo mkdir -p $(BUILD_DIR)/bootstrap/initram-root/root/.ssh
	sudo cp bootstrap/ssh/id_rsa.pub $(BUILD_DIR)/bootstrap/initram-root/root/.ssh/authorized_keys
	sudo chmod 700 $(BUILD_DIR)/bootstrap/initram-root/root/.ssh
	sudo chmod 600 $(BUILD_DIR)/bootstrap/initram-root/root/.ssh/authorized_keys
	sudo mkdir -p $(NAILGUN_DIR)/bin
	sudo cp -r bin/agent $(NAILGUN_DIR)/bin
	sudo mkdir -p $(BUILD_DIR)/bootstrap/initram-root/usr/libexec/mcollective/mcollective/agent/
	sudo cp mcagent/* $(BUILD_DIR)/bootstrap/initram-root/usr/libexec/mcollective/mcollective/agent/
	sudo sh -c "echo bootstrap > $(BUILD_DIR)/bootstrap/initram-root/etc/nailgun_systemtype"
	sudo rm -rf $(BUILD_DIR)/bootstrap/initram-root/home/*

$(BUILD_DIR)/bootstrap/init.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/bootstrap/initram-root/etc/yum.repos.d/mirror.repo
	sudo mkdir -p $(BUILD_DIR)/bootstrap/initram-root/proc $(BUILD_DIR)/bootstrap/initram-root/dev
	sudo mkdir -p $(BUILD_DIR)/bootstrap/initram-root/var/lib/rpm
	$(RPM) --rebuilddb
	$(YUM) install $(YUM_PACKAGES) $(YUM_BUILD_PACKAGES)
	sudo touch $(BUILD_DIR)/bootstrap/initram-root/etc/fstab

	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'kernel-2.*' | xargs rpm2cpio | \
        ( cd $(BUILD_DIR)/bootstrap/initram-root; sudo cpio -idm './lib/modules/*' './boot/vmlinuz*' )
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'kernel-firmware-2.*' | xargs rpm2cpio | \
        ( cd $(BUILD_DIR)/bootstrap/initram-root; sudo cpio -idm './lib/firmware/*' )
	for version in `ls -1 $(BUILD_DIR)/bootstrap/initram-root/lib/modules`; do \
          sudo depmod -b $(BUILD_DIR)/bootstrap/initram-root $$version; \
	done

	sudo mkdir -p $(BUILD_DIR)/bootstrap/initram-root/tmp/gems
	sudo rsync -a --delete $(LOCAL_MIRROR_GEMS)/ $(BUILD_DIR)/bootstrap/initram-root/tmp/gems
	$(CHROOT_CMD) gem install --no-rdoc --no-ri --source file:///tmp/gems \
	httpclient ohai json_pure
	sudo rm -rf $(BUILD_DIR)/bootstrap/initram-root/tmp/gems $(BUILD_DIR)/bootstrap/initram-root/usr/lib/ruby/gems/1.8/cache/*

	sudo mkdir -p $(BUILD_DIR)/bootstrap/initram-root/src
	$(YUM) erase $(YUM_BUILD_PACKAGES)
	sudo rm -f $(BUILD_DIR)/bootstrap/initram-root/etc/yum.repos.d/Cent*
	sudo cp $(BUILD_DIR)/bootstrap/initram-root/sbin/init $(BUILD_DIR)/bootstrap/initram-root/init
	$(CHROOT_CMD) chkconfig exim off
	$(ACTION.TOUCH)

define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(shell readlink -f -m $(LOCAL_MIRROR_CENTOS_OS_BASEURL))
gpgcheck=0
enabled=1
endef

$(BUILD_DIR)/bootstrap/initram-root/etc/yum.repos.d/mirror.repo: export contents:=$(yum_local_repo)
$(BUILD_DIR)/bootstrap/initram-root/etc/yum.repos.d/mirror.repo: bootstrap/module.mk
	sudo mkdir -p $(@D)
	sudo sh -c "echo \"$${contents}\" > $@"
