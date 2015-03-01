.PHONY: bootstrap clean clean-bootstrap

bootstrap: $(ARTS_DIR)/$(BOOTSTRAP_ART_NAME)

$(ARTS_DIR)/$(BOOTSTRAP_ART_NAME): \
		$(BUILD_DIR)/bootstrap/build.done
	mkdir -p $(@D)
	tar zcf $@ -C $(BUILD_DIR) bootstrap/linux bootstrap/initramfs.img

BOOTSTRAP_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(BOOTSTRAP_ART_NAME))

ifdef BOOTSTRAP_DEP_FILE
$(BUILD_DIR)/bootstrap/build.done: $(BOOTSTRAP_DEP_FILE)
	mkdir -p $(@D)
	tar zxf $(BOOTSTRAP_DEP_FILE) -C $(BUILD_DIR)
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/bootstrap/build.done: \
		$(BUILD_DIR)/bootstrap/linux \
		$(BUILD_DIR)/bootstrap/initramfs.img
	$(ACTION.TOUCH)
endif

INITRAMROOT:=$(BUILD_DIR)/bootstrap/initram-root

BOOTSTRAP_RPMS:=\
	bash \
	bfa-firmware \
	ql2100-firmware \
	ql2200-firmware \
	ql23xx-firmware \
	cronie-noanacron \
	crontabs \
	dhclient \
	dmidecode \
	iputils \
	logrotate \
	mcollective \
	mingetty \
	net-tools \
	ntp \
	ntpdate \
	openssh-clients \
	openssh-server \
	pciutils \
	rsyslog \
	scapy \
	tcpdump \
	vconfig \
	vim-minimal \
	wget


BOOTSTRAP_RPMS_CUSTOM:=\
	nailgun-agent \
	nailgun-mcagents \
	nailgun-net-check \
	fuel-agent \
	python-tasklib

define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(LOCAL_MIRROR_CENTOS_OS_BASEURL)
gpgcheck=0
enabled=1
endef

define bootstrap_yum_conf
[main]
cachedir=$(BUILD_DIR)/bootstrap/cache
keepcache=0
debuglevel=6
logfile=$(BUILD_DIR)/bootstrap/yum.log
exclude=*.i686.rpm
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
pluginpath=$(BUILD_DIR)/bootstrap/etc/yum-plugins
pluginconfpath=$(BUILD_DIR)/bootstrap/etc/yum/pluginconf.d
reposdir=$(BUILD_DIR)/bootstrap/etc/yum.repos.d
endef

YUM:=sudo yum -c $(BUILD_DIR)/bootstrap/etc/yum.conf --exclude=ruby-2.1.1 --installroot=$(INITRAMROOT) -y --nogpgcheck

KERNEL_PATTERN:=kernel-lt-3.10.*
KERNEL_FIRMWARE_PATTERN:=linux-firmware*

clean: clean-bootstrap

clean-bootstrap:
	sudo rm -rf $(INITRAMROOT)



$(BUILD_DIR)/bootstrap/initramfs.img: \
		$(BUILD_DIR)/bootstrap/customize-initram-root.done
	sudo sh -c "cd $(INITRAMROOT) && find . -xdev | cpio --create \
        --format='newc' | gzip -9 > $(BUILD_DIR)/bootstrap/initramfs.img"

$(BUILD_DIR)/bootstrap/linux: $(BUILD_DIR)/mirror/centos/build.done
	mkdir -p $(BUILD_DIR)/bootstrap
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name '$(KERNEL_PATTERN)' | xargs rpm2cpio | \
		(cd $(BUILD_DIR)/bootstrap/; cpio -imd './boot/vmlinuz*')
	mv $(BUILD_DIR)/bootstrap/boot/vmlinuz* $(BUILD_DIR)/bootstrap/linux
	rm -r $(BUILD_DIR)/bootstrap/boot
	touch $(BUILD_DIR)/bootstrap/linux

$(BUILD_DIR)/bootstrap/etc/yum.conf: export contents:=$(bootstrap_yum_conf)
$(BUILD_DIR)/bootstrap/etc/yum.repos.d/base.repo: export contents:=$(yum_local_repo)
$(BUILD_DIR)/bootstrap/etc/yum.conf $(BUILD_DIR)/bootstrap/etc/yum.repos.d/base.repo:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

$(BUILD_DIR)/bootstrap/customize-initram-root.done: $(call depv,BOOTSTRAP_RPMS_CUSTOM)
$(BUILD_DIR)/bootstrap/customize-initram-root.done: \
		$(BUILD_DIR)/packages/rpm/build.done \
		$(BUILD_DIR)/bootstrap/prepare-initram-root.done \
		$(call find-files,$(SOURCE_DIR)/bootstrap/sync) \
		$(BUILD_DIR)/repos/nailgun.done \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/bin/send2syslog.py) \
		$(SOURCE_DIR)/bootstrap/ssh/id_rsa.pub \
		$(BUILD_DIR)/bootstrap/etc/yum.conf \
		$(BUILD_DIR)/bootstrap/etc/yum.repos.d/base.repo

	# Rebuilding rpmdb
	sudo rpm --root=$(INITRAMROOT) --rebuilddb

	# Installing custom rpms
	$(YUM) install $(BOOTSTRAP_RPMS_CUSTOM)

	# Copying custom files
	sudo rsync -rlptDK $(SOURCE_DIR)/bootstrap/sync/ $(INITRAMROOT)
	sudo cp -r $(BUILD_DIR)/repos/nailgun/bin/send2syslog.py $(INITRAMROOT)/usr/bin

	# Enabling pre-init boot interface discovery
	sudo chroot $(INITRAMROOT) chkconfig setup-bootdev on

	# Setting root password into r00tme
	sudo sed -i -e '/^root/c\root:$$6$$oC7haQNQ$$LtVf6AI.QKn9Jb89r83PtQN9fBqpHT9bAFLzy.YVxTLiFgsoqlPY3awKvbuSgtxYHx4RUcpUqMotp.WZ0Hwoj.:15441:0:99999:7:::' $(INITRAMROOT)/etc/shadow

	# Copying rsa key.
	sudo mkdir -p $(INITRAMROOT)/root/.ssh
	sudo cp $(SOURCE_DIR)/bootstrap/ssh/id_rsa.pub $(INITRAMROOT)/root/.ssh/authorized_keys
	sudo chmod 700 $(INITRAMROOT)/root/.ssh
	sudo chmod 600 $(INITRAMROOT)/root/.ssh/authorized_keys

	# Copying bash init files
	sudo cp -f $(INITRAMROOT)/etc/skel/.bash* $(INITRAMROOT)/root/

	# Removing garbage
	sudo rm -rf $(INITRAMROOT)/home/*
	sudo rm -rf \
		$(INITRAMROOT)/var/cache/yum \
		$(INITRAMROOT)/var/lib/yum \
		$(INITRAMROOT)/usr/share/doc \
        $(INITRAMROOT)/usr/share/locale \
	sudo rm -rf $(INITRAMROOT)/tmp/*

	$(ACTION.TOUCH)

$(BUILD_DIR)/bootstrap/prepare-initram-root.done: $(call depv,BOOTSTRAP_RPMS)
$(BUILD_DIR)/bootstrap/prepare-initram-root.done: \
		$(BUILD_DIR)/mirror/centos/build.done \
		$(BUILD_DIR)/packages/rpm/build.done \
		$(BUILD_DIR)/bootstrap/etc/yum.conf \
		$(BUILD_DIR)/bootstrap/etc/yum.repos.d/base.repo

	# Installing centos-release package
	sudo rpm -i --root=$(INITRAMROOT) \
		`find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name "centos-release*rpm" | head -1` || \
		echo "centos-release already installed"

	# Removing default repositories (centos-release package provides them)
	sudo rm -f $(INITRAMROOT)/etc/yum.repos.d/Cent*

	# Rebuilding rpmdb
	sudo rpm --root=$(INITRAMROOT) --rebuilddb

	# Creating some necessary directories
	sudo mkdir -p $(INITRAMROOT)/proc
	sudo mkdir -p $(INITRAMROOT)/dev
	sudo mkdir -p $(INITRAMROOT)/var/lib/rpm

	# Installing rpms
	$(YUM) install $(BOOTSTRAP_RPMS)

	# Disabling mail server (it have been installed as a dependency)
	-sudo chroot $(INITRAMROOT) chkconfig exim off
	-sudo chroot $(INITRAMROOT) chkconfig postfix off

	# Installing kernel modules
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name '$(KERNEL_PATTERN)' | xargs rpm2cpio | \
		( cd $(INITRAMROOT); sudo cpio -idm './lib/modules/*' './boot/vmlinuz*' )
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name '$(KERNEL_FIRMWARE_PATTERN)' | xargs rpm2cpio | \
		( cd $(INITRAMROOT); sudo cpio -idm './lib/firmware/*' )
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'kernel-ib*' | xargs rpm2cpio | \
		( cd $(INITRAMROOT); sudo cpio -idm -f './etc/infiniband/openib.conf' \
		'./etc/init.d/openibd' './etc/modprobe.d/mlnx.conf')
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'libibverbs*' | xargs rpm2cpio | \
		( cd $(INITRAMROOT); sudo cpio -idm './*')
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'libmlx4*OFED*' | xargs rpm2cpio | \
		( cd $(INITRAMROOT); sudo cpio -idm './*' )

	# /etc/depmod.d conf for bootstrap is managed by fuel-main git, in order
	# to include missing ubuntu modules directories for CentOS based images.
	# For more info: http://ubuntuforums.org/showthread.php?t=1960892
	for version in `ls -1 $(INITRAMROOT)/lib/modules`; do \
		sudo depmod -b $(INITRAMROOT) $$version \
		-C $(SOURCE_DIR)/bootstrap/bootstrap_depmod.conf; \
	done

	# Some extra actions
	sudo touch $(INITRAMROOT)/etc/fstab
	sudo cp $(INITRAMROOT)/sbin/init $(INITRAMROOT)/init

	$(ACTION.TOUCH)
