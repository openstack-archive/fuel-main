.PHONY: ubuntu_image clean_ubuntu_image
ubuntu_image: $(BUILD_DIR)/image/ubuntu/build.done

$(BUILD_DIR)/image/ubuntu/build.done: $(BUILD_DIR)/mirror/build.done

clean_ubuntu_image:
	rm -rf $(BUILD_DIR)/image/ubuntu

$(BUILD_DIR)/image/ubuntu/build.done: $(ACTION.TOUCH)
