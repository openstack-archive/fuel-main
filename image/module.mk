.PHONY: image clean_image

include $(SOURCE_DIR)/image/centos/module.mk
include $(SOURCE_DIR)/image/ubuntu/module.mk

image: $(BUILD_DIR)/image/build.done

clean: clean_image
clean_image: clean_centos_image clean_ubuntu_image
	rm -rf $(BUILD_DIR)/image

$(BUILD_DIR)/image/build.done: \
		$(BUILD_DIR)/image/centos/build.done \
		$(BUILD_DIR)/image/ubuntu/build.done
	$(ACTION.TOUCH)
