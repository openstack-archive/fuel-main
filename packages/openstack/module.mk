include $(SOURCE_DIR)/packages/openstack/rpm/module.mk
include $(SOURCE_DIR)/packages/openstack/deb/module.mk

.PHONY: openstack

# Usage:
# (eval (call prepare_openstack_source,package_name,file_name,source_path))
define prepare_openstack_source
$(BUILD_DIR)/openstack/source_$1.done: $(BUILD_DIR)/openstack/sources/$1/$2
$(BUILD_DIR)/openstack/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/openstack/sources/$1 $(BUILD_DIR)/openstack/rpm
	cd $3 && python setup.py sdist -d $(BUILD_DIR)/openstack/sources/$1 && python setup.py --version sdist > $(BUILD_DIR)/openstack/rpm/$1-version-tag
endef

ifneq ($(strip $(BUILD_OPENSTACK_PACKAGES)),)
$(BUILD_DIR)/openstack/source_%.done:
	$(ACTION.TOUCH)

$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call set_vars,$(pkg))))
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call build_repo,$(pkg),$($(call uc,$(pkg))_REPO),$($(call uc,$(pkg))_COMMIT),$($(call uc,$(pkg))_GERRIT_URL),$($(call uc,$(pkg))_GERRIT_COMMIT))))
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call build_repo,$(pkg)-build,$($(call uc,$(pkg))_SPEC_REPO),$($(call uc,$(pkg))_SPEC_COMMIT),$($(call uc,$(pkg))_SPEC_GERRIT_URL),$($(call uc,$(pkg))_SPEC_GERRIT_COMMIT))))
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call prepare_openstack_source,$(pkg),$(pkg)-2014.1.tar.gz,$(BUILD_DIR)/repos/$(pkg))))
endif

ifneq ($(strip $(BUILD_OPENSTACK_PACKAGES)),)
$(BUILD_DIR)/openstack/build.done: \
		$(BUILD_DIR)/openstack/rpm/build.done \
		$(BUILD_DIR)/openstack/deb/build.done
endif

$(BUILD_DIR)/openstack/build.done:
	$(ACTION.TOUCH)

openstack: $(BUILD_DIR)/openstack/build.done

openstack-rpm: $(BUILD_DIR)/openstack/rpm/build.done
openstack-deb: $(BUILD_DIR)/openstack/deb/build.done
