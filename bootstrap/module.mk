.PHONY: bootstrap clean clean-bootstrap

INITRAMROOT:=$(BUILD_DIR)/bootstrap/initram-root

BOOTSTRAP_RPMS:=\
	bash \
	byacc \
	cronie-noanacron \
	crontabs \
	dhclient \
	dmidecode \
	flex \
	gcc \
	iputils \
	make \
	mcollective \
	mingetty \
	net-tools \
	ntp \
	openssh-clients \
	openssh-server \
	rsyslog \
	ruby-devel.x86_64 \
	rubygems \
	scapy \
	tcpdump \
	vconfig \
	vim-minimal \
	wget \


BOOTSTRAP_RPMS_GARBAGE:=\
	byacc \
	flex \
	gcc \
	make \
	ruby-devel.x86_64 \


BOOTSTRAP_RPMS_CUSTOM:=\
	nailgun-agent \
	nailgun-mcagents \
	nailgun-net-check \

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

YUM:=sudo yum -c $(BUILD_DIR)/bootstrap/etc/yum.conf --installroot=$(INITRAMROOT) -y --nogpgcheck

clean: clean-bootstrap

clean-bootstrap:
	sudo rm -rf $(INITRAMROOT)

bootstrap: $(BUILD_DIR)/bootstrap/build.done

$(BUILD_DIR)/bootstrap/build.done: \
		$(BUILD_DIR)/bootstrap/linux \
		$(BUILD_DIR)/bootstrap/initramfs.img
	$(ACTION.TOUCH)

$(BUILD_DIR)/bootstrap/initramfs.img: \
		$(BUILD_DIR)/bootstrap/customize-initram-root.done
	sudo sh -c "cd $(INITRAMROOT) && find . -xdev | cpio --create \
        --format='newc' | gzip -9 > $(BUILD_DIR)/bootstrap/initramfs.img"

$(BUILD_DIR)/bootstrap/linux: $(BUILD_DIR)/mirror/build.done
	mkdir -p $(BUILD_DIR)/bootstrap
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'kernel-2.*' | xargs rpm2cpio | \
		(cd $(BUILD_DIR)/bootstrap/; cpio -imd './boot/vmlinuz*')
	mv $(BUILD_DIR)/bootstrap/boot/vmlinuz* $(BUILD_DIR)/bootstrap/linux
	rm -r $(BUILD_DIR)/bootstrap/boot
	touch $(BUILD_DIR)/bootstrap/linux

$(BUILD_DIR)/bootstrap/etc/yum.conf: export contents:=$(bootstrap_yum_conf)
$(BUILD_DIR)/bootstrap/etc/yum.repos.d/base.repo: export contents:=$(yum_local_repo)
$(BUILD_DIR)/bootstrap/etc/yum.conf $(BUILD_DIR)/bootstrap/etc/yum.repos.d/base.repo:
	mkdir -p $(@D)
	echo "$${contents}" > $@

$(BUILD_DIR)/bootstrap/customize-initram-root.done: $(call depv,BOOTSTRAP_RPMS_CUSTOM)
$(BUILD_DIR)/bootstrap/customize-initram-root.done: \
		$(BUILD_DIR)/packages/rpm/build.done \
		$(BUILD_DIR)/bootstrap/prepare-initram-root.done \
		$(call find-files,$(SOURCE_DIR)/bootstrap/sync) \
		$(SOURCE_DIR)/bin/send2syslog.py \
		$(SOURCE_DIR)/bootstrap/ssh/id_rsa.pub \
		$(BUILD_DIR)/bootstrap/etc/yum.conf \
		$(BUILD_DIR)/bootstrap/etc/yum.repos.d/base.repo

	# Rebuilding rpmdb
	sudo rpm --root=$(INITRAMROOT) --rebuilddb

	# Installing custom rpms
	$(YUM) install $(BOOTSTRAP_RPMS_CUSTOM)

	# Copying custom files
	sudo rsync -aK $(SOURCE_DIR)/bootstrap/sync/ $(INITRAMROOT)
	sudo cp -r $(SOURCE_DIR)/bin/send2syslog.py $(INITRAMROOT)/usr/bin

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
		$(BUILD_DIR)/mirror/build.done \
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
	$(YUM) install $(BOOTSTRAP_RPMS) $(BOOTSTRAP_RPMS_TEMPORARY)

	# Installing gems
	sudo mkdir -p $(INITRAMROOT)/tmp/gems
	sudo rsync -a --delete $(LOCAL_MIRROR_GEMS)/ $(INITRAMROOT)/tmp/gems
	sudo chroot $(INITRAMROOT) gem install httpclient --version 2.2.5  --no-rdoc --no-ri --source file:///tmp/gems
	sudo chroot $(INITRAMROOT) gem install ipaddress  --version 0.8.0  --no-rdoc --no-ri --source file:///tmp/gems
	sudo chroot $(INITRAMROOT) gem install json_pure  --version 1.7.5  --no-rdoc --no-ri --source file:///tmp/gems
	sudo chroot $(INITRAMROOT) gem install ohai       --version 6.14.0 --no-rdoc --no-ri --source file:///tmp/gems
	sudo chroot $(INITRAMROOT) gem install rethtool   --version 0.0.3  --no-rdoc --no-ri --source file:///tmp/gems
	sudo rm -rf \
		$(INITRAMROOT)/tmp/gems \
		$(INITRAMROOT)/usr/lib/ruby/gems/1.8/cache/*

	# Removing temporary rpms (devel packages, they were needed to install gems)
	$(YUM) erase $(BOOTSTRAP_RPMS_GARBAGE)

	# Disabling mail server (it have been installed as a dependency)
	-sudo chroot $(INITRAMROOT) chkconfig exim off
	-sudo chroot $(INITRAMROOT) chkconfig postfix off

	# Installing kernel modules
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'kernel-2.*' | xargs rpm2cpio | \
		( cd $(INITRAMROOT); sudo cpio -idm './lib/modules/*' './boot/vmlinuz*' )
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'kernel-firmware-2.*' | xargs rpm2cpio | \
		( cd $(INITRAMROOT); sudo cpio -idm './lib/firmware/*' )
	for version in `ls -1 $(INITRAMROOT)/lib/modules`; do \
		sudo depmod -b $(INITRAMROOT) $$version; \
	done

	# Some extra actions
	sudo touch $(INITRAMROOT)/etc/fstab
	sudo cp $(INITRAMROOT)/sbin/init $(INITRAMROOT)/init

	$(ACTION.TOUCH)
