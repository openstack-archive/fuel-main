include $(SOURCE_DIR)/naily/module.mk
include $(SOURCE_DIR)/astute/module.mk

.PHONY: astute astute_version \
		naily naily_version

RAEMON_VERSION:=0.3.0
RAEMON_COMMIT:=b78eaae57c8e836b8018386dd96527b8d9971acc

$(BUILD_DIR)/packages/gems/build.done: \
		$(call depv,BUILD_MIRROR_GEMS) \
		$(BUILD_DIR)/packages/gems/naily-$(NAILY_VERSION).gem \
		$(BUILD_DIR)/packages/gems/astute-$(ASTUTE_VERSION).gem \
		$(BUILD_DIR)/packages/gems/raemon-$(RAEMON_VERSION).gem
	mkdir -p $(BUILD_MIRROR_GEMS)/gems
	cp $(BUILD_DIR)/packages/gems/*.gem $(BUILD_MIRROR_GEMS)/gems
	(cd $(BUILD_MIRROR_GEMS) && gem generate_index gems)
	$(ACTION.TOUCH)

astute: $(BUILD_DIR)/packages/gems/astute-$(ASTUTE_VERSION).gem
astute_version:
	@echo $(ASTUTE_VERSION)

naily: $(BUILD_DIR)/packages/gems/naily-$(NAILY_VERSION).gem
naily_version:
	@echo $(NAILY_VERSION)

$(BUILD_DIR)/packages/gems/raemon-$(RAEMON_VERSION).gem:
	unzip -q $(LOCAL_MIRROR_SRC)/$(RAEMON_COMMIT).zip -d $(BUILD_DIR)/packages/gems
	rm -rf $(BUILD_DIR)/packages/gems/raemon
	mv $(BUILD_DIR)/packages/gems/raemon-$(RAEMON_COMMIT) $(BUILD_DIR)/packages/gems/raemon
	(cd $(BUILD_DIR)/packages/gems/raemon && gem build raemon.gemspec)
	cp $(BUILD_DIR)/packages/gems/raemon/raemon-$(RAEMON_VERSION).gem $(BUILD_DIR)/packages/gems
