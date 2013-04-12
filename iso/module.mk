.PHONY: iso img
all: iso img

ISOROOT:=$(BUILD_DIR)/iso/isoroot
ISOBASENAME:=nailgun-centos-6.3-amd64
ISONAME:=$(BUILD_DIR)/iso/$(ISOBASENAME).iso
IMGNAME:=$(BUILD_DIR)/iso/$(ISOBASENAME).img

iso: $(BUILD_DIR)/iso/iso.done
img: $(BUILD_DIR)/iso/img.done

$(BUILD_DIR)/iso/isoroot-centos.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
	mkdir -p $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/	$(ISOROOT)
	createrepo -g $(ISOROOT)/repodata/comps.xml \
		-u media://`head -1 $(ISOROOT)/.discinfo` $(ISOROOT)
	$(ACTION.TOUCH)

$(BUILD_DIR)/iso/isoroot-eggs.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done
	mkdir -p $(ISOROOT)/eggs
	rsync -a --delete $(LOCAL_MIRROR_EGGS)/ $(ISOROOT)/eggs
	$(ACTION.TOUCH)

$(BUILD_DIR)/iso/isoroot-gems.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done
	mkdir -p $(ISOROOT)/gems
	rsync -a --delete $(LOCAL_MIRROR_GEMS)/ $(ISOROOT)/gems
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
		$(ISOROOT)/ks.cfg \
		$(ISOROOT)/bootstrap_admin_node.sh \
		$(ISOROOT)/bootstrap_admin_node.conf \
		$(ISOROOT)/version.yaml \
		$(ISOROOT)/puppet-nailgun.tgz \
		$(ISOROOT)/puppet-slave.tgz
	$(ACTION.TOUCH)

$(ISOROOT)/.discinfo: $(SOURCE_DIR)/iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: $(SOURCE_DIR)/iso/.treeinfo ; $(ACTION.COPY)
$(ISOROOT)/isolinux/isolinux.cfg: $(SOURCE_DIR)/iso/isolinux/isolinux.cfg ; $(ACTION.COPY)
$(ISOROOT)/ks.cfg: $(SOURCE_DIR)/iso/ks.cfg ; $(ACTION.COPY)
$(ISOROOT)/bootstrap_admin_node.sh: $(SOURCE_DIR)/iso/bootstrap_admin_node.sh ; $(ACTION.COPY)
$(ISOROOT)/bootstrap_admin_node.conf: $(SOURCE_DIR)/iso/bootstrap_admin_node.conf ; $(ACTION.COPY)
$(ISOROOT)/version.yaml: $(call depv,COMMIT_SHA)
$(ISOROOT)/version.yaml: $(call depv,PRODUCT_VERSION)
$(ISOROOT)/version.yaml:
	echo "COMMIT_SHA: $(COMMIT_SHA)" > $@
	echo "PRODUCT_VERSION: $(PRODUCT_VERSION)" >> $@

$(ISOROOT)/puppet-nailgun.tgz: \
		$(call find-files,$(SOURCE_DIR)/puppet) \
		$(SOURCE_DIR)/bin/send2syslog.py
	(cd $(SOURCE_DIR)/puppet && tar chzf $@ *)
$(ISOROOT)/puppet-slave.tgz: \
		$(call find-files,$(SOURCE_DIR)/puppet/nailytest) \
		$(call find-files,$(SOURCE_DIR)/puppet/osnailyfacter) \
		$(call find-files,$(SOURCE_DIR)/fuel/deployment/puppet)
	(cd $(SOURCE_DIR)/puppet && tar cf $(ISOROOT)/puppet-slave.tar nailytest osnailyfacter)
	(cd $(SOURCE_DIR)/fuel/deployment/puppet && tar rf $(ISOROOT)/puppet-slave.tar ./*)
	gzip -c -9 $(ISOROOT)/puppet-slave.tar > $@ && \
		rm $(ISOROOT)/puppet-slave.tar


########################
# Bootstrap image.
########################

BOOTSTRAP_FILES:=initramfs.img linux

$(BUILD_DIR)/iso/isoroot-bootstrap.done: \
		$(ISOROOT)/bootstrap/bootstrap.rsa \
		$(addprefix $(ISOROOT)/bootstrap/, $(BOOTSTRAP_FILES))
	$(ACTION.TOUCH)

$(addprefix $(ISOROOT)/bootstrap/, $(BOOTSTRAP_FILES)): \
		$(BUILD_DIR)/bootstrap/build.done
	@mkdir -p $(@D)
	cp $(BUILD_DIR)/bootstrap/$(@F) $@

$(ISOROOT)/bootstrap/bootstrap.rsa: $(SOURCE_DIR)/bootstrap/ssh/id_rsa ; $(ACTION.COPY)


########################
# Iso image root file system.
########################

$(BUILD_DIR)/iso/isoroot.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/iso/isoroot-centos.done \
		$(BUILD_DIR)/iso/isoroot-eggs.done \
		$(BUILD_DIR)/iso/isoroot-gems.done \
		$(BUILD_DIR)/iso/isoroot-files.done \
		$(BUILD_DIR)/iso/isoroot-bootstrap.done
	$(ACTION.TOUCH)


########################
# Building CD and USB stick images
########################

# keep in mind that mkisofs touches some files inside directory
# from which it builds iso image
# that is why we need to make isoroot.done dependent on some files
# and then copy these files into another directory
$(BUILD_DIR)/iso/iso.done: $(BUILD_DIR)/iso/isoroot.done
	rm -f $(ISONAME)
	mkdir -p $(BUILD_DIR)/iso/isoroot-mkisofs
	rsync -a --delete $(ISOROOT)/ $(BUILD_DIR)/iso/isoroot-mkisofs
	mkisofs -r -V "Mirantis FuelWeb" -p "Mirantis Inc." \
		-J -T -R -b isolinux/isolinux.bin \
		-no-emul-boot \
		-boot-load-size 4 -boot-info-table \
		-x "lost+found" -o $(ISONAME) $(BUILD_DIR)/iso/isoroot-mkisofs
	implantisomd5 $(ISONAME)
	$(ACTION.TOUCH)

# IMGSIZE is calculated as a sum of nailgun iso size plus
# installation images directory size (~165M) and syslinux directory size (~35M)
# plus a bit of free space for ext2 filesystem data
# +300M seems reasonable
IMGSIZE = $(shell echo "$(shell ls -s $(ISONAME) | awk '{print $$1}') / 1024 + 300" | bc)

$(BUILD_DIR)/iso/img.done: $(BUILD_DIR)/iso/iso.done
	rm -f $(BUILD_DIR)/iso/img_loop_device
	rm -f $(BUILD_DIR)/iso/img_loop_partition
	rm -f $(BUILD_DIR)/iso/img_loop_uuid
	sudo losetup -j $(IMGNAME) | awk -F: '{print $$1}' | while read loopdevice; do \
        sudo kpartx -v $$loopdevice | awk '{print "/dev/mapper/" $$1}' | while read looppartition; do \
            sudo umount -f $$looppartition; \
        done; \
        sudo kpartx -d $$loopdevice; \
        sudo losetup -d $$loopdevice; \
    done
	rm -f $(IMGNAME)
	dd if=/dev/zero of=$(IMGNAME) bs=1M count=$(IMGSIZE)
	sudo losetup -f > $(BUILD_DIR)/iso/img_loop_device
	sudo losetup `cat $(BUILD_DIR)/iso/img_loop_device` $(IMGNAME)
	sudo parted -s `cat $(BUILD_DIR)/iso/img_loop_device` mklabel msdos
	sudo parted -s `cat $(BUILD_DIR)/iso/img_loop_device` unit MB mkpart primary ext2 1 $(IMGSIZE) set 1 boot on
	sudo kpartx -a -v `cat $(BUILD_DIR)/iso/img_loop_device` | awk '{print "/dev/mapper/" $$3}' > $(BUILD_DIR)/iso/img_loop_partition
	sleep 1
	sudo mkfs.ext2 `cat $(BUILD_DIR)/iso/img_loop_partition`
	mkdir -p $(BUILD_DIR)/iso/imgroot
	sudo mount `cat $(BUILD_DIR)/iso/img_loop_partition` $(BUILD_DIR)/iso/imgroot
	sudo extlinux -i $(BUILD_DIR)/iso/imgroot
	sudo /sbin/blkid -s UUID -o value `cat $(BUILD_DIR)/iso/img_loop_partition` > $(BUILD_DIR)/iso/img_loop_uuid
	sudo dd conv=notrunc bs=440 count=1 if=/usr/lib/extlinux/mbr.bin of=`cat $(BUILD_DIR)/iso/img_loop_device`
	sudo cp -r $(BUILD_DIR)/iso/isoroot/images $(BUILD_DIR)/iso/imgroot
	sudo cp -r $(BUILD_DIR)/iso/isoroot/isolinux $(BUILD_DIR)/iso/imgroot
	sudo mv $(BUILD_DIR)/iso/imgroot/isolinux $(BUILD_DIR)/iso/imgroot/syslinux
	sudo rm $(BUILD_DIR)/iso/imgroot/syslinux/isolinux.cfg
	sudo cp $(SOURCE_DIR)/iso/syslinux/syslinux.cfg $(BUILD_DIR)/iso/imgroot/syslinux
	sudo sed -i -e "s/will_be_substituted_with_actual_uuid/`cat $(BUILD_DIR)/iso/img_loop_uuid`/g" $(BUILD_DIR)/iso/imgroot/syslinux/syslinux.cfg
	sudo cp $(SOURCE_DIR)/iso/ks.cfg $(BUILD_DIR)/iso/imgroot/ks.cfg
	sudo sed -i -e "s/will_be_substituted_with_actual_uuid/`cat $(BUILD_DIR)/iso/img_loop_uuid`/g" $(BUILD_DIR)/iso/imgroot/ks.cfg
	sudo cp $(ISONAME) $(BUILD_DIR)/iso/imgroot/nailgun.iso
	sudo sync
	sudo umount `cat $(BUILD_DIR)/iso/img_loop_partition`
	sudo kpartx -d `cat $(BUILD_DIR)/iso/img_loop_device`
	sudo losetup -d `cat $(BUILD_DIR)/iso/img_loop_device`
	$(ACTION.TOUCH)
