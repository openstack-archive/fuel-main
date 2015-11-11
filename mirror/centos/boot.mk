ISOLINUX_FILES:=boot.msg grub.conf initrd.img isolinux.bin memtest vesamenu.c32 vmlinuz
IMAGES_FILES:=efiboot.img boot.iso
LIVEOS_FILES:=squashfs.img
PXEBOOT_FILES:=initrd.img vmlinuz
EFI_FILES:=BOOTX64.EFI MokManager.efi grub.cfg grubx64.efi

MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
MIRROR_CENTOS_KERNEL_BASEURL?=$(MIRROR_CENTOS_KERNEL)/os/$(CENTOS_ARCH)

# centos isolinux files
$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/isolinux/,$(ISOLINUX_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(MIRROR_CENTOS_KERNEL_BASEURL)/isolinux/$(@F)
	mv $@.tmp $@

# centos EFI boot images
$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/EFI/BOOT/,$(EFI_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(MIRROR_CENTOS_KERNEL_BASEURL)/EFI/BOOT/$(@F)
	mv $@.tmp $@

# centos boot images
$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/images/,$(IMAGES_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(MIRROR_CENTOS_KERNEL_BASEURL)/images/$(@F)
	mv $@.tmp $@

# centos pxeboot images
$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/images/pxeboot/,$(PXEBOOT_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(MIRROR_CENTOS_KERNEL_BASEURL)/images/pxeboot/$(@F)
	mv $@.tmp $@

# centos liveos images
$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/LiveOS/,$(LIVEOS_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(MIRROR_CENTOS_KERNEL_BASEURL)/LiveOS/$(@F)
	mv $@.tmp $@

$(BUILD_DIR)/mirror/centos/boot.done: \
		$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/images/,$(IMAGES_FILES)) \
		$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/EFI/BOOT/,$(EFI_FILES)) \
		$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/isolinux/,$(ISOLINUX_FILES)) \
		$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/images/pxeboot/,$(PXEBOOT_FILES)) \
		$(addprefix $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/LiveOS/,$(LIVEOS_FILES))
	$(ACTION.TOUCH)
