NETBOOT_PATH=$(LOCAL_MIRROR)/ubuntu/installer-amd64/current/images/netboot/ubuntu-installer/amd64
$(BUILD_DIR)/packages/deb/debian-boot/initrd.done:\
		$(BUILD_DIR)/mirror/ubuntu/boot.done
	mkdir -p $(@D)
	cd $(@D) && gunzip -c $(NETBOOT_PATH)/initrd.gz | sudo cpio -di
	cd $(@D) && sudo patch -p1 < $(SOURCE_DIR)/packages/deb/debian-boot/preseed-retry.patch
	cd $(@D) && sudo find . | sudo cpio --create --format='newc' > $(BUILD_DIR)/packages/deb/debian-boot/initrd.gz
	$(ACTION.TOUCH)
