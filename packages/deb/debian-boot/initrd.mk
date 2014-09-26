$(BUILD_DIR)/packages/ubuntu/initrd.done:\
		$(BUILD_DIR)/mirror/ubuntu/boot.done
	@mkdir -p $(@D)
	cd $(@D) && gunzip -c $(BUILD_DIR)/mirror/ubuntu/initrd.gz | cpio -di 
	cd $(@D) && patch -p1 $(SOURCE_DIR)/packages/deb/debian-boot/preseed-retry.patch
	cd $(@D) && find . | cpio --create --format='newc' > $(BUILD_DIR)/mirror/ubuntu/initrd.gz
	$(ACTION.TOUCH)
