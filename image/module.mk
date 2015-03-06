.PHONY: image

include $(SOURCE_DIR)/image/centos/module.mk
include $(SOURCE_DIR)/image/ubuntu/module.mk

########################
# TARGET IMAGE ARTIFACT
########################

image: $(BUILD_DIR)/image/build.done
image-ubuntu: $(BUILD_DIR)/image/ubuntu/build.done
image-centos: $(BUILD_DIR)/image/centos/build.done

$(BUILD_DIR)/image/ubuntu/build.done: $(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME)
	$(ACTION.TOUCH)

$(BUILD_DIR)/image/centos/build.done: $(ARTS_DIR)/$(TARGET_CENTOS_IMG_ART_NAME)
	$(ACTION.TOUCH)

# We are going to build ubuntu images on the master node.
# That is the reason why only centos images are set here
# as a prerequisite.
$(BUILD_DIR)/image/build.done: \
	$(BUILD_DIR)/image/centos/build.done
	$(ACTION.TOUCH)
