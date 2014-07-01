$(BUILD_DIR)/image/ubuntu/build.done: $(BUILD_DIR)/mirror/build.done

$(BUILD_DIR)/image/ubuntu/build.done:
    # here are supposed to be commands building ubuntu image
    $(ACTION.TOUCH)
