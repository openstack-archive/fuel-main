$(addprefix $(LOCAL_MIRROR_SRC)/, $(notdir $(REQUIRED_SRCS))):
	@mkdir -p $(LOCAL_MIRROR_SRC)
ifeq ($(MIRROR_SRC),internet)
	wget --no-use-server-timestamps -c -P $(LOCAL_MIRROR_SRC) $(shell echo $(REQUIRED_SRCS) | grep $(notdir $@))
else
	wget --no-use-server-timestamps -c -P $(LOCAL_MIRROR_SRC) $(MIRROR_SRC)/$(notdir $@)
endif

#
# Download ostf packages directry from the github, because
# it updates often and we don't want to update main mirrors
# on each commit
#
$(BUILD_DIR)/mirror/src/build.done: $(call depv,OSTF_TESTS_SHA)
$(BUILD_DIR)/mirror/src/build.done: $(call depv,OSTF_PLUGIN_SHA)
$(BUILD_DIR)/mirror/src/build.done: $(SOURCE_DIR)/requirements-src.txt \
		| $(addprefix $(LOCAL_MIRROR_SRC)/, $(notdir $(REQUIRED_SRCS)))
	wget --no-use-server-timestamps -c -P $(LOCAL_MIRROR_SRC) https://github.com/Mirantis/fuel-ostf-tests/archive/$(OSTF_TESTS_SHA).zip
	wget --no-use-server-timestamps -c -P $(LOCAL_MIRROR_SRC) https://github.com/Mirantis/fuel-ostf-plugin/archive/$(OSTF_PLUGIN_SHA).zip
	$(ACTION.TOUCH)
