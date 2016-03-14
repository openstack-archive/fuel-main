.PHONY: all iso listing
.DELETE_ON_ERROR: $(ISO_PATH)

all: iso listing

ISOROOT:=$(BUILD_DIR)/iso/isoroot

iso: $(ISO_PATH)

listing: $(BUILD_DIR)/iso/isoroot.done $(BUILD_DIR)/mirror/build.done
	-find $(BUILD_DIR) > $(BUILD_DIR)/listing-build.txt
	-find $(LOCAL_MIRROR) > $(BUILD_DIR)/listing-local-mirror.txt
	-find $(BUILD_DIR)/iso/isoroot \
		-regextype posix-egrep \
		-regex '.*(fuel|astute|network-checker|nailgun|shotgun).*\.rpm' | \
			while read package_file; do \
				echo; \
				echo $$(basename $$package_file); \
				rpm -q --changelog -p $$package_file | head -12; \
			done > $(BUILD_DIR)/listing-package-changelog.txt

###################
# BUILD IDENTIFIERS
###################

ifdef BUILD_NUMBER
$(BUILD_DIR)/iso/isoroot.done: $(ISOROOT)/fuel_build_number
$(ISOROOT)/fuel_build_number:
	echo "$(BUILD_NUMBER)" > $@
endif

ifdef BUILD_ID
$(BUILD_DIR)/iso/isoroot.done: $(ISOROOT)/fuel_build_id
$(ISOROOT)/fuel_build_id:
	echo "$(BUILD_ID)" > $@
endif

###############
# CENTOS MIRROR
###############
$(BUILD_DIR)/iso/isoroot-centos.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/mirror/make-changelog.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
	mkdir -p $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/ $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR_MOS_CENTOS) $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR)/extra-repos $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR)/centos-packages.changelog $(ISOROOT)
	$(ACTION.TOUCH)

###############
# UBUNTU MIRROR
###############
$(BUILD_DIR)/iso/isoroot-ubuntu.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/mirror/make-changelog.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
	mkdir -p $(ISOROOT)/ubuntu
	rsync -rp $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/ $(ISOROOT)/ubuntu/
	rsync -rp $(LOCAL_MIRROR)/ubuntu-packages.changelog $(ISOROOT)
	$(ACTION.TOUCH)

########################
# Extra files
########################

$(BUILD_DIR)/iso/isoroot-dotfiles.done: \
		$(ISOROOT)/.discinfo \
		$(ISOROOT)/.treeinfo
	$(ACTION.TOUCH)

$(BUILD_DIR)/iso/isoroot-files.done: \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done \
		$(ISOROOT)/isolinux/isolinux.cfg \
		$(ISOROOT)/isolinux/splash.jpg \
		$(ISOROOT)/ks.cfg
	$(ACTION.TOUCH)

$(ISOROOT)/.discinfo: $(SOURCE_DIR)/iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: $(SOURCE_DIR)/iso/.treeinfo ; $(ACTION.COPY)

$(ISOROOT)/ks.yaml:
	@mkdir -p $(@D)
	cp $(KSYAML) $@

$(ISOROOT)/isolinux/isolinux.cfg: $(SOURCE_DIR)/iso/isolinux/isolinux.cfg ; $(ACTION.COPY)
$(ISOROOT)/isolinux/splash.jpg: $(call depv,FEATURE_GROUPS)
ifeq ($(filter mirantis,$(FEATURE_GROUPS)),mirantis)
$(ISOROOT)/isolinux/splash.jpg: $(SOURCE_DIR)/iso/isolinux/splash.jpg ; $(ACTION.COPY)
else
$(ISOROOT)/isolinux/splash.jpg: $(SOURCE_DIR)/iso/isolinux/splash_community.jpg ; $(ACTION.COPY)
endif
$(ISOROOT)/ks.cfg: $(SOURCE_DIR)/iso/ks.template $(SOURCE_DIR)/iso/ks.py $(ISOROOT)/ks.yaml
	python $(SOURCE_DIR)/iso/ks.py \
		-t $(SOURCE_DIR)/iso/ks.template \
		-c $(ISOROOT)/ks.yaml \
		-u '{"CENTOS_RELEASE": "$(CENTOS_RELEASE)", "PRODUCT_VERSION": "$(PRODUCT_VERSION)"}' \
		-o $@.tmp
	mv $@.tmp $@


########################
# Iso image root file system.
########################

$(BUILD_DIR)/iso/isoroot.done: \
		$(BUILD_DIR)/iso/isoroot-centos.done \
		$(BUILD_DIR)/iso/isoroot-ubuntu.done \
		$(BUILD_DIR)/iso/isoroot-files.done
	$(ACTION.TOUCH)

########################
# Building CD and USB stick images
########################

# ISO_VOLUME_ID can't have whitespaces or other non-alphanumeric characters 'as is'.
# They must be represented as \xNN, where NN is the hexadecimal representation of the character.
# For example, \x20 is a white space (" ").
# This is the limitation of kickstart boot options.

ifeq ($(filter mirantis,$(FEATURE_GROUPS)),mirantis)
ISO_VOLUME_ID:=Mirantis_Fuel
ISO_VOLUME_PREP:="Mirantis Inc."
else
ISO_VOLUME_ID:=OpenStack_Fuel
ISO_VOLUME_PREP:="Fuel team"
endif

# keep in mind that mkisofs touches some files inside directory
# from which it builds iso image
# that is why we need to make isoroot.done dependent on some files
# and then copy these files into another directory
$(ISO_PATH): $(BUILD_DIR)/iso/isoroot.done
	rm -f $@
	mkdir -p $(BUILD_DIR)/iso/isoroot-mkisofs $(@D)
	rsync -a --delete $(ISOROOT)/ $(BUILD_DIR)/iso/isoroot-mkisofs
	sudo sed -r -i -e "s/ip=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/ip=$(MASTER_IP)/" $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	sudo sed -r -i -e "s/dns1=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/dns1=$(MASTER_DNS)/" $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	sudo sed -r -i -e "s/netmask=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/netmask=$(MASTER_NETMASK)/" $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	sudo sed -r -i -e "s/gw=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/gw=$(MASTER_GW)/" $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	sudo sed -r -i -e "s/will_be_substituted_with_PRODUCT_VERSION/$(PRODUCT_VERSION)/" $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	sudo sed -r -i -e 's/will_be_substituted_with_ISO_VOLUME_ID/$(ISO_VOLUME_ID)/g' $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	sudo sed -r -i -e 's/will_be_substituted_with_ISO_VOLUME_ID/$(ISO_VOLUME_ID)/g' $(BUILD_DIR)/iso/isoroot-mkisofs/ks.cfg


	mkdir -p $(BUILD_DIR)/iso/efi_tmp/efi_image
	# We need to have a partition which will be pointed from ISO as efi partition
	# vmlinuz + initrd + bootloader + conffile = about 38MB. 100M should be enough ^_^
	dd bs=1M count=100 if=/dev/zero of=$(BUILD_DIR)/iso/efi_tmp/efiboot.img
	# UEFI standard say to us that EFI partition should be some FAT-related filesystem
	mkfs.vfat $(BUILD_DIR)/iso/efi_tmp/efiboot.img
	sudo umount -l $(BUILD_DIR)/iso/efi_tmp/efi_image || true
	sudo mount $(BUILD_DIR)/iso/efi_tmp/efiboot.img $(BUILD_DIR)/iso/efi_tmp/efi_image

	# This needs to be edited in place due to some strange implemntations of UEFI
	# For example, Tianocore OVMF will not use efiboot.img. Instead, it looks for
	# bootloader and it conffiles in /EFI/BOOT/* on main ISO partition (with ISO9660 fs)
	echo > $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf
	echo "default=0" >> $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf
	#echo "splashimage=/EFI/BOOT/splash.xpm.gz" >> $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf
	echo "timeout 300" >> $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf
	echo "hiddenmenu" >> $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf
	echo "title DVD Fuel Install (Static IP)" >> $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf
	# efiboot.img is a partition with filesystem now and /vmlinuz there will be pointed
	# to root of it
	echo "  kernel /vmlinuz biosdevname=0 ks=cdrom:/ks.cfg ip=$(MASTER_IP) gw=$(MASTER_GW) dns1=$(MASTER_DNS) netmask=$(MASTER_NETMASK) hostname=fuel.domain.tld showmenu=yes" >> $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf
	echo "  initrd /initrd.img" >> $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf
	echo "title USB Fuel Install (Static IP)" >> $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf
	echo "  kernel /vmlinuz biosdevname=0 repo=hd:LABEL=\"$(ISO_VOLUME_ID)\":/ ks=hd:LABEL=\"$(ISO_VOLUME_ID)\":/ks.cfg ip=$(MASTER_IP) gw=$(MASTER_GW) dns1=$(MASTER_DNS) netmask=$(MASTER_NETMASK) hostname=fuel.domain.tld showmenu=yes" >> $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf
	echo "  initrd /initrd.img" >> $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf

	# But many UEFI implementations will use our efiboot.img and if we want to boot from it,
	# we also need to place kernel and initrd there (and bootloader and conffile to it too)
	sudo cp -f $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/vmlinuz $(BUILD_DIR)/iso/efi_tmp/efi_image/
	sudo cp -f $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/initrd.img $(BUILD_DIR)/iso/efi_tmp/efi_image/
	sudo mkdir -p $(BUILD_DIR)/iso/efi_tmp/efi_image/EFI/BOOT/
	sudo cp -f $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.conf $(BUILD_DIR)/iso/efi_tmp/efi_image/EFI/BOOT/
	sudo cp -f $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/BOOTX64.EFI $(BUILD_DIR)/iso/efi_tmp/efi_image/EFI/BOOT/
	#sudo cp -f $(BUILD_DIR)/iso/isoroot-mkisofs/EFI/BOOT/splash.xpm.gz $(BUILD_DIR)/iso/efi_tmp/efi_image/EFI/BOOT/
	sudo umount $(BUILD_DIR)/iso/efi_tmp/efi_image
	cp -f $(BUILD_DIR)/iso/efi_tmp/efiboot.img $(BUILD_DIR)/iso/isoroot-mkisofs/images/
	sudo rm -rf $(BUILD_DIR)/iso/efi_tmp/

	xorriso -as mkisofs \
		-V $(ISO_VOLUME_ID) -p $(ISO_VOLUME_PREP) \
		-J -R \
		-graft-points \
		-b isolinux/isolinux.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
		-isohybrid-mbr /usr/lib/syslinux/isohdpfx.bin \
		-eltorito-alt-boot -e images/efiboot.img -no-emul-boot \
		-isohybrid-gpt-basdat \
		-o $@ $(BUILD_DIR)/iso/isoroot-mkisofs
	implantisomd5 $@
