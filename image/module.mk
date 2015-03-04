.PHONY: image

include $(SOURCE_DIR)/image/centos/module.mk

########################
# TARGET IMAGE ARTIFACT
########################

image: $(BUILD_DIR)/image/build.done
image-centos: $(BUILD_DIR)/image/centos/build.done

$(BUILD_DIR)/image/centos/build.done: $(ARTS_DIR)/$(TARGET_CENTOS_IMG_ART_NAME)
	$(ACTION.TOUCH)

$(BUILD_DIR)/image/build.done: \
	$(BUILD_DIR)/image/centos/build.done
	$(ACTION.TOUCH)
