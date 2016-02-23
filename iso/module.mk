.PHONY: all iso listing
.DELETE_ON_ERROR: $(ISO_PATH)

all: iso listing

ISO_PATH?=$(ARTS_DIR)/$(ISO_NAME).iso

iso: $(ISO_PATH)

##################
# INFRA ARTIFACTS
##################
$(ARTS_DIR)/config.yaml: $(CONFIG_YAML); $(ACTION.COPY)
$(ARTS_DIR)/centos_mirror.yaml: $(CENTOS_MIRROR_YAML); $(ACTION.COPY)
$(ARTS_DIR)/ubuntu_mirror.yaml: $(UBUNTU_MIRROR_YAML); $(ACTION.COPY)

$(ARTS_DIR)/listing-package-changelog.txt: $(BUILD_DIR)/iso/isoroot.done
	@mkdir -p $(@D)
	find $(BUILD_DIR)/iso/isoroot \
		-regextype posix-egrep \
		-regex '.*(fuel|astute|network-checker|nailgun|packetary|shotgun).*\.rpm' | \
			while read package_file; do \
				echo; \
				echo $$(basename $$package_file); \
				rpm -q --changelog -p $$package_file | head -12; \
			done > $@.tmp
	mv $@.tmp $@

listing: \
		$(ARTS_DIR)/listing-package-changelog.txt \
		$(ARTS_DIR)/config.yaml \
		$(ARTS_DIR)/centos_mirror.yaml \
		$(ARTS_DIR)/ubuntu_mirror.yaml

###################
# BUILD IDENTIFIERS
###################
ifdef BUILD_NUMBER
$(BUILD_DIR)/iso/isoroot.done: $(ISOROOT)/fuel_build_number
$(ISOROOT)/fuel_build_number:
	@mkdir -p $(@D)
	echo "$(BUILD_NUMBER)" > $@
endif

$(BUILD_DIR)/iso/isoroot.done: $(ISOROOT)/fuel_build_id
$(ISOROOT)/fuel_build_id:
	@mkdir -p $(@D)
	echo "$(BUILD_ID)" > $@

#########
# IMAGES
#########
# TODO(kozhukalov): implement downloading images in python
IMAGES_BASEURL?=$(CENTOS_URL)/os/x86_64/
IMAGES?=\
isolinux/boot.msg \
isolinux/grub.conf \
isolinux/initrd.img \
isolinux/isolinux.bin \
isolinux/memtest \
isolinux/vesamenu.c32 \
isolinux/vmlinuz \
images/efiboot.img \
images/boot.iso \
images/pxeboot/initrd.img \
images/pxeboot/vmlinuz \
EFI/BOOT/BOOTX64.EFI \
EFI/BOOT/MokManager.efi \
EFI/BOOT/grub.cfg \
EFI/BOOT/grubx64.efi \
LiveOS/squashfs.img

# centos boot images
$(addprefix $(ISOROOT)/,$(IMAGES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(IMAGES_BASEURL)/$(subst $(ISOROOT)/,,$@)
	mv $@.tmp $@

$(BUILD_DIR)/iso/isoroot-images.done: $(addprefix $(ISOROOT)/,$(IMAGES))
	$(ACTION.TOUCH)

#########
# MIRROR
#########
$(BUILD_DIR)/mirror-changelog.done: $(BUILD_DIR)/mirror.done
	env LOCAL_MIRROR=$(ISOROOT) $(SOURCE_DIR)/report-changelog.sh
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror.done: \
		$(BUILD_DIR)/centos_mirror.done \
		$(BUILD_DIR)/ubuntu_mirror.done
	$(ACTION.TOUCH)

$(BUILD_DIR)/centos_mirror.done: $(CENTOS_MIRROR_YAML)
	@mkdir -p $(ISOROOT)
	packetary --threads-num 10 clone \
		-t rpm \
		-r $(CENTOS_MIRROR_YAML) \
		-R $(SOURCE_DIR)/yaml/centos_packages.yaml \
		-d $(ISOROOT)
	$(ACTION.TOUCH)

$(BUILD_DIR)/ubuntu_mirror.done: $(UBUNTU_MIRROR_YAML)
	@mkdir -p $(ISOROOT)
	packetary --threads-num 10 clone \
		-t deb \
		-r $(UBUNTU_MIRROR_YAML) \
		-R $(SOURCE_DIR)/yaml/ubuntu_packages.yaml \
		-d $(ISOROOT)
	$(ACTION.TOUCH)

$(BUILD_DIR)/iso/isoroot-mirror.done: \
		$(BUILD_DIR)/mirror.done \
		$(BUILD_DIR)/mirror-changelog.done
	$(ACTION.TOUCH)

##############
# CUSTOM REPOS
##############

define default_deb_repos
- name: mos
  suite: $(MIRROR_MOS_UBUNTU_SUITE)
endef

$(ISOROOT)/default_deb_repos.yaml: export default_deb_repos_content:=$(default_deb_repos)
$(ISOROOT)/default_deb_repos.yaml:
	/bin/echo -e "$${default_deb_repos_content}\n" > $@

########################
# EXTRA FILES
########################
$(ISOROOT)/.discinfo: $(SOURCE_DIR)/iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: $(SOURCE_DIR)/iso/.treeinfo ; $(ACTION.COPY)
$(ISOROOT)/isolinux/splash.jpg: $(SOURCE_DIR)/iso/isolinux/splash.jpg; $(ACTION.COPY)

$(ISOROOT)/isolinux/isolinux.cfg: $(CONFIG_YAML)
	@mkdir -p $(@D)
	python $(SOURCE_DIR)/evaluator.py \
		-t $(SOURCE_DIR)/iso/isolinux/isolinux.cfg \
		-c $(CONFIG_YAML) \
		-o $@.tmp
	mv $@.tmp $@

$(ISOROOT)/ks.cfg: $(SOURCE_DIR)/iso/ks.cfg $(CONFIG_YAML)
	@mkdir -p $(@D)
	python $(SOURCE_DIR)/evaluator.py \
		-t $(SOURCE_DIR)/iso/ks.cfg \
		-c $(CONFIG_YAML) \
		-o $@.tmp
	mv $@.tmp $@

$(BUILD_DIR)/iso/isoroot-files.done: \
		$(ISOROOT)/.discinfo \
		$(ISOROOT)/.treeinfo \
		$(ISOROOT)/default_deb_repos.yaml \
		$(ISOROOT)/isolinux/splash.jpg \
		$(ISOROOT)/isolinux/isolinux.cfg \
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
