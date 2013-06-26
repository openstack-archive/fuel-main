ISOLINUX_FILES:=boot.msg grub.conf initrd.img isolinux.bin memtest splash.jpg vesamenu.c32 vmlinuz
IMAGES_FILES:=efiboot.img efidisk.img install.img
EFI_FILES:=BOOTX64.conf BOOTX64.efi splash.xpm.gz

# isolinux files
$(addprefix $(LOCAL_MIRROR_RHEL)/isolinux/,$(ISOLINUX_FILES)):
	@mkdir -p $(@D)
	wget -O $@ $(MIRROR_RHEL_BOOT)/isolinux/$(@F)

# EFI boot images
$(addprefix $(LOCAL_MIRROR_RHEL)/EFI/BOOT/,$(EFI_FILES)):
	@mkdir -p $(@D)
	wget -O $@ $(MIRROR_RHEL_BOOT)/EFI/BOOT/$(@F)

# boot images
$(addprefix $(LOCAL_MIRROR_RHEL)/images/,$(IMAGES_FILES)):
	@mkdir -p $(@D)
	wget -O $@ $(MIRROR_RHEL_BOOT)/images/$(@F)

$(BUILD_DIR)/mirror/rhel/boot.done: \
		$(addprefix $(LOCAL_MIRROR_RHEL)/images/,$(IMAGES_FILES)) \
		$(addprefix $(LOCAL_MIRROR_RHEL)/EFI/BOOT/,$(EFI_FILES)) \
		$(addprefix $(LOCAL_MIRROR_RHEL)/isolinux/,$(ISOLINUX_FILES))
	$(ACTION.TOUCH)
