include $(SOURCE_DIR)/mirror/src/config.mk

$(addprefix $(LOCAL_MIRROR_SRC)/, $(notdir $(SRC_URLS))):
	@mkdir -p $(LOCAL_MIRROR_SRC)
	wget --no-use-server-timestamps -c -P $(LOCAL_MIRROR_SRC) $(shell echo $(SRC_URLS) | grep $(notdir $@))

$(BUILD_DIR)/mirror/src/build.done: $(SOURCE_DIR)/requirements-src.txt \
		| $(addprefix $(LOCAL_MIRROR_SRC)/, $(notdir $(SRC_URLS)))
	$(ACTION.TOUCH)
