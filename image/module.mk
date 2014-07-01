.PHONY: image clean_image

image: $(BUILD_DIR)/image/build.done

clean:
	rm -rf $(BUILD_DIR)/image

include $(SOURCE_DIR)/image/centos/module.mk
include $(SOURCE_DIR)/image/ubuntu/module.mk

$(BUILD_DIR)/image/build.done: \
		$(BUILD_DIR)/image/centos/build.done \
		$(BUILD_DIR)/image/ubuntu/build.done \
	$(ACTION.TOUCH)
