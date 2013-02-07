include $(SOURCE_DIR)/naily/module.mk
include $(SOURCE_DIR)/astute/module.mk

.PHONY: astute astute_version \
		naily naily_version

$(BUILD_DIR)/packages/gems/build.done: \
		$(BUILD_DIR)/packages/gems/naily-$(NAILY_VERSION).gem \
		$(BUILD_DIR)/packages/gems/astute-$(ASTUTE_VERSION).gem
	mkdir -p $(LOCAL_MIRROR_GEMS)/gems
	find $(BUILD_DIR)/packages/gems/ ! -name "build.done" \
		-exec cp {} $(LOCAL_MIRROR_GEMS)/gems \;
	(cd $(LOCAL_MIRROR_GEMS) && gem generate_index gems)
	$(ACTION.TOUCH)

astute: $(BUILD_DIR)/packages/gems/astute-$(ASTUTE_VERSION).gem
astute_version:
	@echo $(ASTUTE_VERSION)

naily: $(BUILD_DIR)/packages/gems/naily-$(NAILY_VERSION).gem
naily_version:
	@echo $(NAILY_VERSION)