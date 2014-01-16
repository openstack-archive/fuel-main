ISOLINUX_FILES:=boot.msg grub.conf initrd.img isolinux.bin memtest vesamenu.c32 vmlinuz
IMAGES_FILES:=efiboot.img efidisk.img
EFI_FILES:=BOOTX64.conf BOOTX64.efi splash.xpm.gz

# centos isolinux files
$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/isolinux/,$(ISOLINUX_FILES)):
	@mkdir -p $(@D)
	wget -O $@ $(MIRROR_CENTOS_OS_BASEURL)/isolinux/$(@F)

# centos EFI boot images
$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/EFI/BOOT/,$(EFI_FILES)):
	@mkdir -p $(@D)
	wget -O $@ $(MIRROR_CENTOS_OS_BASEURL)/EFI/BOOT/$(@F)

# centos boot images
$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/images/,$(IMAGES_FILES)):
	@mkdir -p $(@D)
	wget -O $@ $(MIRROR_CENTOS_OS_BASEURL)/images/$(@F)

# get custom centos install.img 
  wget http://osci-obs.vm.mirantis.net:82/centos-fuel-4.1-stable/install.img $(MIRROR_CENTOS_OS_BASEURL)/images/install.img

$(BUILD_DIR)/mirror/centos/boot.done: \
		$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/images/,$(IMAGES_FILES)) \
		$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/EFI/BOOT/,$(EFI_FILES)) \
		$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/isolinux/,$(ISOLINUX_FILES))
	$(ACTION.TOUCH)
