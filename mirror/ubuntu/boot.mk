ISOLINUX_FILES:=netboot.tar.gz

# debian isolinux files
$(addprefix $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/installer-amd64/current/images/netboot/,$(ISOLINUX_FILES)):
	@mkdir -p $(@D)
ifeq ($(USE_MIRROR),none)
	wget -O $@ $(MIRROR_UBUNTU)/ubuntu/dists/precise-updates/main/installer-amd64/current/images/trusty-netboot/netboot.tar.gz
else
	wget -O $@ $(MIRROR_UBUNTU)/installer-amd64/current/images/netboot/netboot.tar.gz
endif
	
	tar -xzf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/installer-amd64/current/images/netboot/$(@F) -C $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/installer-amd64/current/images/netboot/

$(BUILD_DIR)/mirror/ubuntu/boot.done: \
		$(addprefix $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/installer-amd64/current/images/netboot/,$(ISOLINUX_FILES))
	$(ACTION.TOUCH)
