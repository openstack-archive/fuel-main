.PHONY: mirror clean clean-mirror make-changelog

mirror: $(BUILD_DIR)/mirror/build.done
make-changelog: $(BUILD_DIR)/mirror/make-changelog.done

clean: clean-mirror

clean-mirror:
	sudo rm -rf $(BUILD_DIR)/mirror

include $(SOURCE_DIR)/mirror/centos/module.mk
include $(SOURCE_DIR)/mirror/ubuntu/module.mk
include $(SOURCE_DIR)/mirror/docker/module.mk
include $(SOURCE_DIR)/mirror/diff_mirror_module.mk

$(BUILD_DIR)/mirror/build.done: \
		$(BUILD_DIR)/mirror/centos/build.done \
		$(BUILD_DIR)/mirror/ubuntu/build.done \
		$(BUILD_DIR)/mirror/docker/build.done
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/make-changelog.done: $(BUILD_DIR)/mirror/build.done
	sudo bash -c "export LOCAL_MIRROR=$(LOCAL_MIRROR); \
		$(SOURCE_DIR)/report-changelog.sh"
	$(ACTION.TOUCH)
