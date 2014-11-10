.PHONY: image

include $(SOURCE_DIR)/image/centos/module.mk
include $(SOURCE_DIR)/image/ubuntu/module.mk

########################
# TARGET IMAGE ARTIFACT
########################

image: $(BUILD_DIR)/image/build.done

$(BUILD_DIR)/image/build.done: $(ARTS_DIR)/$(TARGET_CENTOS_IMG_ART_NAME) $(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME)
	$(ACTION.TOUCH)
