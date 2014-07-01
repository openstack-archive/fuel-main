.PHONY: image

include $(SOURCE_DIR)/image/centos/module.mk
include $(SOURCE_DIR)/image/ubuntu/module.mk

########################
# TARGET IMAGE ARTIFACT
########################

image: $(BUILD_DIR)/image/build.done

$(BUILD_DIR)/image/build.done: target_centos_image target_ubuntu_image
	$(ACTION.TOUCH)
