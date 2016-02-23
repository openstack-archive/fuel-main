.PHONY: all iso listing
.DELETE_ON_ERROR: $(ISO_PATH)

all: iso listing

ISO_PATH?=$(ARTS_DIR)/$(ISO_NAME).iso
ISOROOT:=$(BUILD_DIR)/iso/isoroot

iso: $(ISO_PATH)

##################
# INFRA ARTIFACTS
##################
$(ARTS_DIR)/listing-build.txt: $(BUILD_DIR)/iso/isoroot.done
	mkdir -p $(ARTS_DIR)
	find $(BUILD_DIR) > $@.tmp
	mv $@.tmp $@

$(ARTS_DIR)/listing-package-changelog.txt: $(BUILD_DIR)/iso/isoroot.done
	mkdir -p $(ARTS_DIR)
	find $(BUILD_DIR)/iso/isoroot \
		-regextype posix-egrep \
		-regex '.*(fuel|astute|network-checker|shotgun|nailgun).*\.rpm' | \
			while read package_file; do \
				echo; \
				echo $$(basename $$package_file); \
				rpm -q --changelog -p $$package_file | head -12; \
			done > $@.tmp
	mv $@.tmp $@

listing: $(ARTS_DIR)/listing-build.txt $(ARTS_DIR)/listing-package-changelog.txt


###################
# BUILD IDENTIFIERS
###################
ifdef BUILD_NUMBER
$(BUILD_DIR)/iso/isoroot.done: $(ISOROOT)/fuel_build_number
$(ISOROOT)/fuel_build_number:
	@mkdir -p $(@D)
	echo "$(BUILD_NUMBER)" > $@
endif

ifdef BUILD_ID
$(BUILD_DIR)/iso/isoroot.done: $(ISOROOT)/fuel_build_id
$(ISOROOT)/fuel_build_id:
	@mkdir -p $(@D)
	echo "$(BUILD_ID)" > $@
endif

#########
# IMAGES
#########
# TODO(kozhukalov): implement downloading images in python
IMAGES_BASEURL?=$(call $(notdir $(MIRROR_YAML))_0_url)
ISOLINUX_FILES:=boot.msg grub.conf initrd.img isolinux.bin memtest vesamenu.c32 vmlinuz
IMAGES_FILES:=efiboot.img boot.iso
LIVEOS_FILES:=squashfs.img
PXEBOOT_FILES:=initrd.img vmlinuz
EFI_FILES:=BOOTX64.EFI MokManager.efi grub.cfg grubx64.efi

# centos isolinux files
$(addprefix $(ISOROOT)/isolinux/,$(ISOLINUX_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(IMAGES_BASEURL)/isolinux/$(@F)
	mv $@.tmp $@

# centos EFI boot images
$(addprefix $(ISOROOT)/EFI/BOOT/,$(EFI_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(IMAGES_BASEURL)/EFI/BOOT/$(@F)
	mv $@.tmp $@

# centos boot images
$(addprefix $(ISOROOT)/images/,$(IMAGES_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(IMAGES_BASEURL)/images/$(@F)
	mv $@.tmp $@

# centos pxeboot images
$(addprefix $(ISOROOT)/images/pxeboot/,$(PXEBOOT_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(IMAGES_BASEURL)/images/pxeboot/$(@F)
	mv $@.tmp $@

# centos liveos images
$(addprefix $(ISOROOT)/LiveOS/,$(LIVEOS_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(IMAGES_BASEURL)/LiveOS/$(@F)
	mv $@.tmp $@

$(BUILD_DIR)/iso/isoroot-images.done: \
		$(addprefix $(ISOROOT)/images/,$(IMAGES_FILES)) \
		$(addprefix $(ISOROOT)/EFI/BOOT/,$(EFI_FILES)) \
		$(addprefix $(ISOROOT)/isolinux/,$(ISOLINUX_FILES)) \
		$(addprefix $(ISOROOT)/images/pxeboot/,$(PXEBOOT_FILES)) \
		$(addprefix $(ISOROOT)/LiveOS/,$(LIVEOS_FILES))
	$(ACTION.TOUCH)

#########
# MIRROR
#########
$(BUILD_DIR)/mirror-changelog.done: $(BUILD_DIR)/mirror.done
	bash -c "export LOCAL_MIRROR=$(ISOROOT); \
		$(SOURCE_DIR)/report-changelog.sh"
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror.done:
	@mkdir -p $(ISOROOT)
	packetary --threads-num 10 serial-clone -f $(MIRROR_YAML) -d $(ISOROOT)
	$(ACTION.TOUCH)

$(BUILD_DIR)/iso/isoroot-mirror.done: \
		$(BUILD_DIR)/mirror.done \
		$(BUILD_DIR)/mirror-changelog.done
	$(ACTION.TOUCH)

########################
# EXTRA FILES
########################
$(ISOROOT)/.discinfo: $(SOURCE_DIR)/iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: $(SOURCE_DIR)/iso/.treeinfo ; $(ACTION.COPY)

$(BUILD_DIR)/iso/isoroot-dotfiles.done: \
		$(ISOROOT)/.discinfo \
		$(ISOROOT)/.treeinfo
	$(ACTION.TOUCH)

$(ISOROOT)/isolinux/isolinux.cfg:
	@mkdir -p $(@D)
	python $(SOURCE_DIR)/evaluator.py \
		-t $(SOURCE_DIR)/iso/isolinux/isolinux.cfg \
		-c $(CONFIG_YAML) \
		-o $@.tmp
	mv $@.tmp $@

$(ISOROOT)/isolinux/splash.jpg: \
		$(SOURCE_DIR)/iso/isolinux/splash.jpg
	$(ACTION.COPY)

$(ISOROOT)/ks.cfg: $(SOURCE_DIR)/iso/ks.cfg
	@mkdir -p $(@D)
	python $(SOURCE_DIR)/evaluator.py \
		-t $(SOURCE_DIR)/iso/ks.cfg \
		-c $(CONFIG_YAML) \
		-o $@.tmp
	mv $@.tmp $@

$(BUILD_DIR)/iso/isoroot-files.done: \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done \
		$(ISOROOT)/isolinux/isolinux.cfg \
		$(ISOROOT)/isolinux/splash.jpg \
		$(ISOROOT)/ks.cfg
	$(ACTION.TOUCH)

########################
# Iso image root file system.
########################
$(BUILD_DIR)/iso/isoroot.done: \
		$(BUILD_DIR)/iso/isoroot-images.done \
		$(BUILD_DIR)/iso/isoroot-mirror.done \
		$(BUILD_DIR)/iso/isoroot-files.done
	$(ACTION.TOUCH)

########################
# Building CD and USB stick images
########################

# keep in mind that mkisofs touches some files inside directory
# from which it builds iso image
# that is why we need to make isoroot.done dependent on some files
# and then copy these files into another directory
$(ISO_PATH): $(BUILD_DIR)/iso/isoroot.done
	rm -f $@
	mkdir -p $(BUILD_DIR)/iso/isoroot-mkisofs $(@D)
	rsync -a --delete $(ISOROOT)/ $(BUILD_DIR)/iso/isoroot-mkisofs

	mkdir -p $(BUILD_DIR)/iso/efi_tmp/efi_image
	# We need to have a partition which will be pointed from ISO as efi partition
	# vmlinuz + initrd + bootloader + conffile = about 38MB. 100M should be enough ^_^
	dd bs=1M count=100 if=/dev/zero of=$(BUILD_DIR)/iso/efi_tmp/efiboot.img
	# UEFI standard say to us that EFI partition should be some FAT-related filesystem
	mkfs.vfat $(BUILD_DIR)/iso/efi_tmp/efiboot.img
	sudo umount -l $(BUILD_DIR)/iso/efi_tmp/efi_image || true
	sudo mount $(BUILD_DIR)/iso/efi_tmp/efiboot.img $(BUILD_DIR)/iso/efi_tmp/efi_image

	mkdir -p $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT
	python $(SOURCE_DIR)/evaluator.py \
		-t $(SOURCE_DIR)/iso/EFI/BOOT/BOOTX64.conf \
		-c $(CONFIG_YAML) \
		-o $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf

	# But many UEFI implementations will use our efiboot.img and if we want to boot from it,
	# we also need to place kernel and initrd there (and bootloader and conffile to it too)
	sudo cp -f $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/vmlinuz $(BUILD_DIR)/iso/efi_tmp/efi_image/
	sudo cp -f $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/initrd.img $(BUILD_DIR)/iso/efi_tmp/efi_image/
	sudo mkdir -p $(BUILD_DIR)/iso/efi_tmp/efi_image/EFI/BOOT/
	sudo cp -f $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf $(BUILD_DIR)/iso/efi_tmp/efi_image/EFI/BOOT/
	sudo cp -f $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.EFI $(BUILD_DIR)/iso/efi_tmp/efi_image/EFI/BOOT/
	sudo umount $(BUILD_DIR)/iso/efi_tmp/efi_image
	cp -f $(BUILD_DIR)/iso/efi_tmp/efiboot.img $(BUILD_DIR)/iso/isoroot-mkisofs/images/
	sudo rm -rf $(BUILD_DIR)/iso/efi_tmp/

	xorriso -as mkisofs \
		-V "$(ISO_VOLUME_ID)" -p "$(ISO_VOLUME_PREP)" \
		-J -R \
		-graft-points \
		-b isolinux/isolinux.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
		-isohybrid-mbr /usr/lib/syslinux/isohdpfx.bin \
		-eltorito-alt-boot -e images/efiboot.img -no-emul-boot \
		-isohybrid-gpt-basdat \
		-o $@ $(BUILD_DIR)/iso/isoroot-mkisofs
	implantisomd5 $@
