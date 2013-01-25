.PHONY: bootstrap clean
all: bootstrap

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


YUM:=sudo yum --installroot=`readlink -f $(INITRAMROOT)` -y --nogpgcheck

clean: clean-bootstrap

clean-bootstrap:
	sudo rm -rf $(INITRAMROOT)

bootstrap: $(BUILD_DIR)/bootstrap/bootstrap.done

$(BUILD_DIR)/bootstrap/build.done: \
		$(BUILD_DIR)/bootstrap/linux \
		$(BUILD_DIR)/bootstrap/initramfs.img
	$(ACTION.TOUCH)

$(BUILD_DIR)/bootstrap/initramfs.img: \
		$(BUILD_DIR)/bootstrap/customize-initram-root.done
	sudo sh -c "cd $(INITRAMROOT) && find . -xdev | cpio --create \
        --format='newc' | gzip -9 > `readlink -f $(BUILD_DIR)/bootstrap/initramfs.img`"

$(BUILD_DIR)/bootstrap/linux: $(BUILD_DIR)/mirror/build.done
	mkdir -p $(BUILD_DIR)/bootstrap
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'kernel-2.*' | xargs rpm2cpio | \
		(cd $(BUILD_DIR)/bootstrap/; cpio -imd './boot/vmlinuz*')
	mv $(BUILD_DIR)/bootstrap/boot/vmlinuz* $(BUILD_DIR)/bootstrap/linux
	rm -r $(BUILD_DIR)/bootstrap/boot
	touch $(BUILD_DIR)/bootstrap/linux

$(BUILD_DIR)/bootstrap/customize-initram-root.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/bootstrap/prepare-initram-root.done \
		$(call find-files,$(SOURCE_DIR)/bootstrap/sync) \
		$(SOURCE_DIR)/bin/send2syslog.py \
		$(SOURCE_DIR)/bootstrap/ssh/id_rsa.pub

	# Installing custom rpms
	$(YUM) install $(BOOTSTRAP_RPMS_CUSTOM)

	# Copying custom files
	sudo rsync -a $(SOURCE_DIR)/bootstrap/sync/ $(INITRAMROOT)
	sudo cp -r $(SOURCE_DIR)/bin/send2syslog.py $(INITRAMROOT)/usr/bin

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
	sudo rm -f $(INITRAMROOT)/etc/yum.repos.d/mirror.repo
	sudo rm -rf \
		$(INITRAMROOT)/var/cache/yum \
		$(INITRAMROOT)/var/lib/yum \
		$(INITRAMROOT)/usr/share/doc \
        $(INITRAMROOT)/usr/share/locale \

	$(ACTION.TOUCH)


define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(shell readlink -f -m $(LOCAL_MIRROR_CENTOS_OS_BASEURL))
gpgcheck=0
enabled=1
endef


$(BUILD_DIR)/bootstrap/prepare-initram-root.done: export yum_local_repo:=$(yum_local_repo)
$(BUILD_DIR)/bootstrap/prepare-initram-root.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done

	# Creating some necessary directories
	sudo mkdir -p $(INITRAMROOT)/proc
	sudo mkdir -p $(INITRAMROOT)/dev
	sudo mkdir -p $(INITRAMROOT)/var/lib/rpm

	# Defining local repository in order to install rpms
	sudo mkdir -p $(INITRAMROOT)/etc/yum.repos.d
	sudo sh -c "echo \"$${yum_local_repo}\" > $(INITRAMROOT)/etc/yum.repos.d/mirror.repo"

	# Removing default repositories and rebuilding rpm database
	sudo rm -f $(INITRAMROOT)/etc/yum.repos.d/Cent*
	sudo rpm --root=`readlink -f $(INITRAMROOT)` --rebuilddb

	# Installing rpms
	$(YUM) install $(BOOTSTRAP_RPMS) $(BOOTSTRAP_RPMS_TEMPORARY)

	# Installing gems
	sudo mkdir -p $(INITRAMROOT)/tmp/gems
	sudo rsync -a --delete $(LOCAL_MIRROR_GEMS)/ $(INITRAMROOT)/tmp/gems
	sudo chroot $(INITRAMROOT) gem install --no-rdoc --no-ri --source file:///tmp/gems \
		httpclient ohai json_pure
	sudo rm -rf \
		$(INITRAMROOT)/tmp/gems \
		$(INITRAMROOT)/usr/lib/ruby/gems/1.8/cache/*

	# Removing temporary rpms (devel packages, they were needed to install gems)
	$(YUM) erase $(BOOTSTRAP_RPMS_GARBAGE)

	# Disabling exim (it have been installed as a dependency)
	sudo chroot $(INITRAMROOT) chkconfig exim off

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
