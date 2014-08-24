include $(SOURCE_DIR)/bootstrap/mock_config.mk

.PHONY: bootstrap clean clean-bootstrap

CHROOT_TMP:=/var/tmp

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

BOOTSTRAP_RPMS_INIT:=centos-release

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
	openssh-clients \
	openssh-server \
	pciutils \
	rsyslog \
	scapy \
	tcpdump \
	vconfig \
	vim-minimal \
	wget \
	tar \
	rsync


BOOTSTRAP_RPMS_CUSTOM:=\
	nailgun-agent \
	nailgun-mcagents \
	nailgun-net-check


KERNEL_PATTERN:=kernel-lt-3.10.*
KERNEL_FIRMWARE_PATTERN:=linux-firmware*

clean: clean-bootstrap

clean-bootstrap:
	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--scrub=all


$(BUILD_DIR)/bootstrap/initramfs.img: \
		$(BUILD_DIR)/bootstrap/customize-initram-root.done
	sudo sh -c "cd /var/lib/mock/fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH)/root && \
				find . -xdev | cpio --create --format='newc' \
        | gzip -9 > $(BUILD_DIR)/bootstrap/initramfs.img"

$(BUILD_DIR)/bootstrap/linux: $(BUILD_DIR)/mirror/build.done
	mkdir -p $(BUILD_DIR)/bootstrap
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name '$(KERNEL_PATTERN)' | xargs rpm2cpio | \
		(cd $(BUILD_DIR)/bootstrap/; cpio -imd './boot/vmlinuz*')
	mv $(BUILD_DIR)/bootstrap/boot/vmlinuz* $(BUILD_DIR)/bootstrap/linux
	rm -r $(BUILD_DIR)/bootstrap/boot
	touch $(BUILD_DIR)/bootstrap/linux

$(BUILD_DIR)/bootstrap/mock/customize_initram_root.sh: $(call depv,bootstrap-customize-initram-root)
$(BUILD_DIR)/bootstrap/mock/customize_initram_root.sh: export contents:=$(bootstrap-customize-initram-root)
$(BUILD_DIR)/bootstrap/mock/customize_initram_root.sh:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@
	chmod +x $@

$(BUILD_DIR)/bootstrap/customize-initram-root.done: $(call depv,BOOTSTRAP_RPMS_CUSTOM)
$(BUILD_DIR)/bootstrap/customize-initram-root.done: \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/bootstrap/prepare-initram-root.done \
		$(call find-files,$(SOURCE_DIR)/bootstrap/sync) \
		$(BUILD_DIR)/repos/nailgun.done \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/bin/send2syslog.py) \
		$(SOURCE_DIR)/bootstrap/ssh/id_rsa.pub \
		$(BUILD_DIR)/bootstrap/mock/customize_initram_root.sh

	# Installing custom rpms
	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--install $(BOOTSTRAP_RPMS_CUSTOM)

	# Preparing custom files
	tar -czvf $(BUILD_DIR)/bootstrap/bootstrap-customize.tgz \
	$(SOURCE_DIR)/bootstrap/sync/ \
	$(BUILD_DIR)/repos/nailgun/bin/send2syslog.py \
	$(SOURCE_DIR)/bootstrap/ssh/id_rsa.pub

	# Copy custom files and working script to chroot $(CHROOT_TMP)
	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--copyin $(BUILD_DIR)/bootstrap/bootstrap-customize.tgz \
		$(BUILD_DIR)/bootstrap/mock/customize_initram_root.sh \
		$(CHROOT_TMP)

	# run customization script in chroot
	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--shell "$(CHROOT_TMP)/customize_initram_root.sh"

	$(ACTION.TOUCH)


# main config file, can be empty and options can be passed using command line
$(BUILD_DIR)/bootstrap/mock/site-defaults.cfg: $(call depv,bootstrap-mock-site-defaults)
$(BUILD_DIR)/bootstrap/mock/site-defaults.cfg: export contents:=$(bootstrap-mock-site-defaults)
$(BUILD_DIR)/bootstrap/mock/site-defaults.cfg:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

# mock logging files
$(BUILD_DIR)/bootstrap/mock/logging.ini: $(call depv,bootstrap-mock-logging)
$(BUILD_DIR)/bootstrap/mock/logging.ini: export contents:=$(bootstrap-mock-logging)
$(BUILD_DIR)/bootstrap/mock/logging.ini:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

# main mock file config
$(BUILD_DIR)/bootstrap/mock/fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH).cfg: $(call depv,bootstrap-mock-fuel-config)
$(BUILD_DIR)/bootstrap/mock/fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH).cfg: export contents:=$(bootstrap-mock-fuel-config)
$(BUILD_DIR)/bootstrap/mock/fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH).cfg:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

$(BUILD_DIR)/bootstrap/mock/install_kernel_modules.sh: export contents:=$(bootstrap-install-modules)
$(BUILD_DIR)/bootstrap/mock/install_kernel_modules.sh:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@
	chmod +x $@

	# let's provide all targets for running mock
$(BUILD_DIR)/bootstrap/mock/mock-config.done: \
		$(BUILD_DIR)/bootstrap/mock/site-defaults.cfg \
		$(BUILD_DIR)/bootstrap/mock/logging.ini \
		$(BUILD_DIR)/bootstrap/mock/fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH).cfg
	$(ACTION.TOUCH)


$(BUILD_DIR)/bootstrap/prepare-initram-root.done: $(call depv,BOOTSTRAP_RPMS)
$(BUILD_DIR)/bootstrap/prepare-initram-root.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/bootstrap/mock/mock-config.done \
		$(BUILD_DIR)/bootstrap/mock/install_kernel_modules.sh

	# prepare chroot
	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--init

	# Init bootstrap env and installing centos-release package
	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--install $(BOOTSTRAP_RPMS_INIT)

	# Removing default repositories (centos-release package provides them)
	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--shell "rm -f /etc/yum.repos.d/CentOS-*"

	# Installing rpms
	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--install $(BOOTSTRAP_RPMS)


	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--shell "chkconfig exim off ; chkconfig postfix off"


	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--copyin `find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name '$(KERNEL_PATTERN)'` \
		`find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name '$(KERNEL_FIRMWARE_PATTERN)'` \
		`find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name 'libmlx4*'` \
		$(BUILD_DIR)/bootstrap/mock/install_kernel_modules.sh /var/tmp

	# Install kernel modules
	# please check content of $(BUILD_DIR)/bootstrap/mock/install_kernel_modules.sh
	/usr/bin/mock --configdir=$(BUILD_DIR)/bootstrap/mock \
	-r fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--shell "$(CHROOT_TMP)/install_kernel_modules.sh"

	$(ACTION.TOUCH)
