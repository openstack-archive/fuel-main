.PHONY: mirror clean clean-mirror mirror-pkgs-changelog

mirror: $(BUILD_DIR)/mirror/build.done
mirror-pkgs-changelog: $(BUILD_DIR)/mirror/mirror-pkgs-changelog.done

clean: clean-mirror

clean-mirror:
	sudo rm -rf $(BUILD_DIR)/mirror

include $(SOURCE_DIR)/mirror/centos/module.mk
include $(SOURCE_DIR)/mirror/ubuntu/module.mk
include $(SOURCE_DIR)/mirror/docker/module.mk

$(BUILD_DIR)/mirror/build.done: \
		$(BUILD_DIR)/mirror/centos/build.done \
		$(BUILD_DIR)/mirror/ubuntu/build.done \
		$(BUILD_DIR)/mirror/docker/build.done
	$(ACTION.TOUCH)

# generate list of packages from mirrors
$(BUILD_DIR)/mirror/mirror-pkgs-changelog.done: \
		$(BUILD_DIR)/mirror/ubuntu/mirror.done \
		$(BUILD_DIR)/mirror/centos/build.done
	bash -c "export LOCAL_MIRROR=$(LOCAL_MIRROR); \
		export CENTOS_FILE=centos-mirror-packages.changelog; \
		export UBUNTU_FILE=ubuntu-mirror-packages.changelog; \
		$(SOURCE_DIR)/report-changelog.sh"
	$(ACTION.TOUCH)
