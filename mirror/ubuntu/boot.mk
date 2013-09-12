ISOLINUX_FILES:=netboot.tar.gz

# debian isolinux files
$(addprefix $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/,$(ISOLINUX_FILES)):
	@mkdir -p $(ISO_DIR)/isoroot/ubuntu/installer-amd64/current/images/netboot $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)
	wget -O $@ $(MIRROR_UBUNTU_OS_BASEURL)/installer-amd64/current/images/netboot/$(@F)
	tar -xzf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/$(@F) -C $(ISO_DIR)/isoroot/ubuntu/installer-amd64/current/images/netboot

$(BUILD_DIR)/mirror/ubuntu/boot.done: \
		$(addprefix $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/,$(ISOLINUX_FILES))
	$(ACTION.TOUCH)
