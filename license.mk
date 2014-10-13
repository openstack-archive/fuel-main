.PHONY: license

license: $(BUILD_DIR)/license/license.done

$(BUILD_DIR)/license/license.done: \
        $(BUILD_DIR)/license/deb.done\
        $(BUILD_DIR)/license/rpm.done
	$(ACTION.TOUCH)

$(BUILD_DIR)/license/deb.done: \
	$(BUILD_DIR)/repos/repos.done
	mkdir -p $(@D)
	$(SOURCE_DIR)/utils/license/deb_license.sh detail $(LOCAL_MIRROR_UBUNTU)/pool/main/* > $(BUILD_DIR)/license/deb.rst

$(BUILD_DIR)/license/rpm.done: \
	$(BUILD_DIR)/repos/repos.done
	mkdir -p $(@D)
	$(SOURCE_DIR)/utils/license/rpm_license.sh $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages/* > $(BUILD_DIR)/license/rpm.rst
