.PHONY: mirror-ubuntu repo-ubuntu

mirror-ubuntu: $(BUILD_DIR)/mirror/ubuntu/mirror.done
repo-ubuntu: $(BUILD_DIR)/mirror/ubuntu/repo.done

define reprepro_dist_conf
Origin: Mirantis
Label: $(PRODUCT_NAME)$(PRODUCT_VERSION)
Suite: $(PRODUCT_NAME)$(PRODUCT_VERSION)
Codename: $(PRODUCT_NAME)$(PRODUCT_VERSION)
Description: Mirantis OpenStack mirror
Architectures: $(UBUNTU_ARCH)
Components: main restricted
DebIndices: Packages Release . .gz .bz2
Update: - $(PRODUCT_NAME)$(PRODUCT_VERSION)
endef

define reprepro_updates_conf
Suite: $(PRODUCT_NAME)$(PRODUCT_VERSION)
Name: $(PRODUCT_NAME)$(PRODUCT_VERSION)
Method: file:$(LOCAL_MIRROR_UBUNTU)
Components: main
Architectures: $(UBUNTU_ARCH)
VerifyRelease: blindtrust
endef



# Two operation modes:
# USE_MIRROR=none - mirroring mode, rsync full mirror from internal build server
# USE_MIRROR=<any_other_value> - ISO building mode, get repository for current product release only
$(BUILD_DIR)/mirror/ubuntu/build.done: 	$(BUILD_DIR)/mirror/ubuntu/mirror.done
ifneq ($(BUILD_PACKAGES),0)
    $(BUILD_DIR)/mirror/ubuntu/build.done:	$(BUILD_DIR)/mirror/ubuntu/repo.done
endif

REPREPRO_CONF_DIR:=$(BUILD_DIR)/mirror/ubuntu/reprepro/conf

define config_reprepro
#Generate reprepro distributions config
cat > $(REPREPRO_CONF_DIR)/distributions << EOF
$(reprepro_dist_conf)
EOF
#Generate reprepro updates config
cat > $(REPREPRO_CONF_DIR)/updates << EOF
$(reprepro_updates_conf)
EOF
endef

$(BUILD_DIR)/mirror/ubuntu/reprepro_config.done: export config_reprepro:=$(config_reprepro)
$(BUILD_DIR)/mirror/ubuntu/reprepro_config.done:
	mkdir -p $(REPREPRO_CONF_DIR)
	sh -c "$${config_reprepro}"
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/ubuntu/reprepro.done: \
		$(BUILD_DIR)/mirror/ubuntu/mirror.done \
		$(BUILD_DIR)/mirror/ubuntu/reprepro_config.done
	# Import existing Ubuntu repository
	cd $(LOCAL_MIRROR_UBUNTU) && reprepro --confdir=$(REPREPRO_CONF_DIR) -V update
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/ubuntu/repo.done: \
		$(BUILD_DIR)/mirror/ubuntu/reprepro_config.done \
		$(BUILD_DIR)/mirror/ubuntu/reprepro.done
	# FIXME(aglarendil): do not touch upstream repo. instead - build new repo
	# Import newly built packages
	cd $(LOCAL_MIRROR_UBUNTU) && reprepro --confdir=$(REPREPRO_CONF_DIR) -V includedeb $(PRODUCT_NAME)$(PRODUCT_VERSION) $(BUILD_DIR)/packages/deb/packages/*.deb
	# Clean up reprepro data
	rm -rf $(LOCAL_MIRROR_UBUNTU)/db
	rm -rf $(LOCAL_MIRROR_UBUNTU)/lists
	$(ACTION.TOUCH)

define ubuntu_fuel_dist_conf
Origin: Mirantis
Label: $(PRODUCT_NAME)$(PRODUCT_VERSION)
Suite: $(PRODUCT_NAME)$(PRODUCT_VERSION)
Codename: $(PRODUCT_NAME)$(PRODUCT_VERSION)
Description: Mirantis OpenStack - Fuel packages
Architectures: $(UBUNTU_ARCH)
Components: main
DebIndices: Packages Release . .gz .bz2
Update: - $(PRODUCT_NAME)$(PRODUCT_VERSION)
endef

$(BUILD_DIR)/mirror/fuel/ubuntu.done: export REPREPRO_DISTRO_CONF:=$(ubuntu_fuel_dist_conf)
$(BUILD_DIR)/mirror/fuel/ubuntu.done: FUEL_REPO:=$(LOCAL_MIRROR)/fuel/ubuntu
$(BUILD_DIR)/mirror/fuel/ubuntu.done:
	mkdir -p $(FUEL_REPO)/conf
	echo "$${REPREPRO_DISTRO_CONF}" > $(FUEL_REPO)/conf/distributions
	cd $(FUEL_REPO) && reprepro -Vb. includedeb mos$(PRODUCT_VERSION) $(BUILD_DIR)/packages/deb/packages/*.deb

$(BUILD_DIR)/mirror/ubuntu/mirror.done:
	mkdir -p $(LOCAL_MIRROR_UBUNTU)
ifeq (none,$(strip $(USE_MIRROR)))
	set -ex; rsync -aPtvz $(MIRROR_FUEL_UBUNTU)::$(PRODUCT_NAME)-ubuntu $(LOCAL_MIRROR_UBUNTU)/
else
	set -ex; debmirror --method=$(MIRROR_UBUNTU_METHOD) --progress --checksums --nocleanup --host=$(MIRROR_UBUNTU) --root=$(MIRROR_UBUNTU_ROOT) \
	--arch=$(UBUNTU_ARCH) --dist=$(PRODUCT_NAME)$(PRODUCT_VERSION) --nosource --ignore-release-gpg --rsync-extra=none \
	--section=$(MIRROR_UBUNTU_SECTION) $(LOCAL_MIRROR_UBUNTU)/
	rm -rf $(LOCAL_MIRROR_UBUNTU)/.temp $(LOCAL_MIRROR_UBUNTU)/project
endif
	$(ACTION.TOUCH)
