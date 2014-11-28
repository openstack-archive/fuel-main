ISOLINUX_FILES:=netboot.tar.gz

LOCAL_NETBOOT_DIR:=$(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/installer-amd64/current/images/netboot
LOCAL_NETBOOT_TGZ:=$(LOCAL_NETBOOT_DIR)/$(ISOLINUX_FILES)
NETBOOT_URL:=$(MIRROR_UBUNTU)/installer-amd64/current/images/netboot/netboot.tar.gz
ifeq ($(USE_MIRROR),none)
NETBOOT_URL:=$(MIRROR_UBUNTU)/ubuntu/dists/$(UBUNTU_RELEASE)-updates/main/installer-amd64/current/images/$(UBUNTU_NETBOOT_FLAVOR)/netboot.tar.gz
endif

# debian isolinux files
$(LOCAL_NETBOOT_TGZ):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(NETBOOT_URL)
	mv $@.tmp $@
	tar -xzf $@ -C $(@D)

$(BUILD_DIR)/mirror/ubuntu/boot.done: $(LOCAL_NETBOOT_TGZ)
	$(ACTION.TOUCH)
