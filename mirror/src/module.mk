$(addprefix $(LOCAL_MIRROR_SRC)/, $(notdir $(REQUIRED_SRCS))):
	@mkdir -p $(LOCAL_MIRROR_SRC)
ifndef MIRROR_SRC
	wget --no-use-server-timestamps -c -P $(LOCAL_MIRROR_SRC) $(shell echo $(REQUIRED_SRCS) | grep $(notdir $@))
else
	wget --no-use-server-timestamps -c -P $(LOCAL_MIRROR_SRC) $(MIRROR_SRC)/$(notdir $@)
endif

$(BUILD_DIR)/mirror/src/build.done: $(SOURCE_DIR)/requirements-src.txt \
		| $(addprefix $(LOCAL_MIRROR_SRC)/, $(notdir $(REQUIRED_SRCS)))
	$(ACTION.TOUCH)
