# this file is for building rescue image
# currently it is build manually and we
# just download it

.PHONY: rescue

clean: clean_rescue

clean_rescue:
	rm -rf $(BUILD_DIR)/rescue

rescue: $(BUILD_DIR)/rescue/build.done

$(BUILD_DIR)/rescue/build.done: $(BUILD_DIR)/rescue/linux $(BUILD_DIR)/rescue/initrd
	$(ACTION.TOUCH)

$(BUILD_DIR)/rescue/linux:
	@mkdir -p $(@D)
	wget -O $@  $(MIRROR_RESCUE)/linux
	touch $@

$(BUILD_DIR)/rescue/initrd:
	@mkdir -p $(@D)
	wget -O $@ $(MIRROR_RESCUE)/initrd.cgz
	touch $@
