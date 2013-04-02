include $(SOURCE_DIR)/naily/module.mk
include $(SOURCE_DIR)/astute/module.mk

.PHONY: astute astute_version \
		naily naily_version

$(BUILD_DIR)/packages/gems/build.done: \
		$(BUILD_DIR)/packages/gems/naily-$(NAILY_VERSION).gem \
		$(BUILD_DIR)/packages/gems/astute-$(ASTUTE_VERSION).gem \
		$(BUILD_DIR)/packages/gems/raemon-0.3.0.gem
	mkdir -p $(LOCAL_MIRROR_GEMS)/gems
	cp $(BUILD_DIR)/packages/gems/*.gem $(LOCAL_MIRROR_GEMS)/gems
	(cd $(LOCAL_MIRROR_GEMS) && gem generate_index gems)
	$(ACTION.TOUCH)

astute: $(BUILD_DIR)/packages/gems/astute-$(ASTUTE_VERSION).gem
astute_version:
	@echo $(ASTUTE_VERSION)

naily: $(BUILD_DIR)/packages/gems/naily-$(NAILY_VERSION).gem
naily_version:
	@echo $(NAILY_VERSION)

$(BUILD_DIR)/packages/gems/raemon-0.3.0.gem:
	unzip -q $(LOCAL_MIRROR_SRC)/b78eaae57c8e836b8018386dd96527b8d9971acc.zip -d $(BUILD_DIR)/packages/gems
	rm -rf $(BUILD_DIR)/packages/gems/raemon
	mv $(BUILD_DIR)/packages/gems/raemon-b78eaae57c8e836b8018386dd96527b8d9971acc $(BUILD_DIR)/packages/gems/raemon
	(cd $(BUILD_DIR)/packages/gems/raemon && gem build raemon.gemspec)
	cp $(BUILD_DIR)/packages/gems/raemon/raemon-0.3.0.gem $(BUILD_DIR)/packages/gems
