.PHONY: astute naily

RAEMON_VERSION:=0.3.0
RAEMON_COMMIT:=b78eaae57c8e836b8018386dd96527b8d9971acc

$(BUILD_DIR)/packages/gems/build.done: \
		$(call depv,BUILD_MIRROR_GEMS) \
		$(BUILD_DIR)/packages/gems/naily.done \
		$(BUILD_DIR)/packages/gems/astute.done \
		$(BUILD_DIR)/packages/gems/raemon-$(RAEMON_VERSION).gem
	mkdir -p $(BUILD_MIRROR_GEMS)/gems
	cp $(BUILD_DIR)/packages/gems/*.gem $(BUILD_MIRROR_GEMS)/gems
	(cd $(BUILD_MIRROR_GEMS) && gem generate_index gems)
	$(ACTION.TOUCH)

astute: $(BUILD_DIR)/packages/gems/astute.done

naily: $(BUILD_DIR)/packages/gems/naily.done

$(BUILD_DIR)/packages/gems/raemon-$(RAEMON_VERSION).gem: \
		$(BUILD_DIR)/mirror/build.done
	unzip -q $(LOCAL_MIRROR_SRC)/$(RAEMON_COMMIT).zip -d $(BUILD_DIR)/packages/gems
	rm -rf $(BUILD_DIR)/packages/gems/raemon
	mv $(BUILD_DIR)/packages/gems/raemon-$(RAEMON_COMMIT) $(BUILD_DIR)/packages/gems/raemon
	(cd $(BUILD_DIR)/packages/gems/raemon && gem build raemon.gemspec)
	cp $(BUILD_DIR)/packages/gems/raemon/raemon-$(RAEMON_VERSION).gem $(BUILD_DIR)/packages/gems

$(BUILD_DIR)/packages/gems/astute.done: \
		$(BUILD_DIR)/repos/astute.done \
		$(call find-files,$(BUILD_DIR)/repos/astute/astute.gemspec) \
		$(call find-files,$(BUILD_DIR)/repos/astute/bin) \
		$(call find-files,$(BUILD_DIR)/repos/astute/lib) \
		$(call find-files,$(BUILD_DIR)/repos/astute/spec)
	@mkdir -p $(@D)
	cd $(BUILD_DIR)/repos/astute && gem build astute.gemspec
	mv $(BUILD_DIR)/repos/astute/astute-*.gem $(@D)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/gems/naily.done: \
		$(BUILD_DIR)/repos/nailgun.done \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/naily/naily.gemspec) \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/naily/bin) \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/naily/lib)
	@mkdir -p $(@D)
	cd $(BUILD_DIR)/repos/nailgun/naily && gem build naily.gemspec
	mv $(BUILD_DIR)/repos/nailgun/naily/naily-*.gem $(@D)
	$(ACTION.TOUCH)
