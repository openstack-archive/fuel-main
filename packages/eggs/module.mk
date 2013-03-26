include $(SOURCE_DIR)/nailgun/module.mk

.PHONY: nailgun nailgun_version

$(BUILD_DIR)/packages/eggs/build.done: \
		$(BUILD_DIR)/packages/eggs/Nailgun-$(NAILGUN_VERSION).tar.gz
	mkdir -p $(LOCAL_MIRROR_EGGS)
	find $(BUILD_DIR)/packages/eggs/ -maxdepth 1 -and ! -name "build.done" \
	    -and ! -type d -exec cp {} $(LOCAL_MIRROR_EGGS) \;
	$(ACTION.TOUCH)

nailgun: $(BUILD_DIR)/packages/eggs/Nailgun-$(NAILGUN_VERSION).tar.gz
nailgun_version:
	@echo $(NAILGUN_VERSION)