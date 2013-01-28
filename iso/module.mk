/:=$(BUILD_DIR)/iso/

.PHONY: iso
all: iso

ISOROOT:=$/isoroot
ISOBASENAME:=nailgun-centos-6.3-amd64
ISONAME:=$/$(ISOBASENAME).iso
IMGNAME:=$/$(ISOBASENAME).img

iso: $(ISONAME)
img: $(IMGNAME)

$/isoroot-centos.done: \
		$(BUILD_DIR)/rpm/rpm.done \
		$(LOCAL_MIRROR)/cache.done \
		$(ISOROOT)/repodata/comps.xml \
		$(ISOROOT)/.discinfo \
		$(ISOROOT)/.treeinfo
	mkdir -p $(ISOROOT)/Packages
	find $(CENTOS_REPO_DIR)Packages -name '*.rpm' -exec cp -u {} $(ISOROOT)/Packages \;
	createrepo -g `readlink -f "$(ISOROOT)/repodata/comps.xml"` -u media://`head -1 $(ISOROOT)/.discinfo` $(ISOROOT)
	$(ACTION.TOUCH)

$(ISOROOT)/repodata/comps.xml: | $(CENTOS_REPO_DIR)repodata/comps.xml
	mkdir $(@D)
	cp $(CENTOS_REPO_DIR)repodata/comps.xml $(@D)

$(ISOROOT)/isolinux/isolinux.cfg: iso/isolinux/isolinux.cfg ; $(ACTION.COPY)

$(addprefix $(ISOROOT)/isolinux/,$(ISOLINUX_FILES)): \
		$(LOCAL_MIRROR)/cache-boot.done \
		$(ISOROOT)/isolinux/isolinux.cfg
	cp $(CENTOS_REPO_DIR)/isolinux/$(@F) $(@D)

$/isoroot-isolinux.done: $(addprefix $(ISOROOT)/isolinux/,$(ISOLINUX_FILES))
	$(ACTION.TOUCH)

$(addprefix $(ISOROOT)/images/,$(IMAGES_FILES)):
	@mkdir -p $(@D)
	cp $(CENTOS_REPO_DIR)images/$(@F) $(@D)

$(addprefix $(ISOROOT)/EFI/BOOT/,$(EFI_FILES)):
	@mkdir -p $(@D)
	cp $(CENTOS_REPO_DIR)EFI/BOOT/$(@F) $(@D)

$/isoroot-prepare.done: \
		$(addprefix $(ISOROOT)/images/,$(IMAGES_FILES)) \
		$(addprefix $(ISOROOT)/EFI/BOOT/,$(EFI_FILES)) \
		$(ISOROOT)/ks.cfg \
		$(ISOROOT)/bootstrap_admin_node.sh \
		$(ISOROOT)/bootstrap_admin_node.conf \
		$(ISOROOT)/etc/nailgun/version.yaml
	$(ACTION.TOUCH)

$/isoroot-bootstrap.done: \
		$(ISOROOT)/bootstrap/bootstrap.rsa \
		$(addprefix $(ISOROOT)/bootstrap/, $(BOOTSTRAP_FILES))
	$(ACTION.TOUCH)

$(addprefix $(ISOROOT)/bootstrap/, $(BOOTSTRAP_FILES)): \
		$(BUILD_DIR)/bootstrap/bootstrap.done
	@mkdir -p $(@D)
	cp $(BUILD_DIR)/bootstrap/$(@F) $@

$(ISOROOT)/bootstrap/bootstrap.rsa: bootstrap/ssh/id_rsa ; $(ACTION.COPY)

$(ISOROOT)/eggs/Nailgun-$(NAILGUN_VERSION).tar.gz: $(BUILD_DIR)/nailgun/Nailgun-$(NAILGUN_VERSION).tar.gz ; $(ACTION.COPY)
$(ISOROOT)/gems/gems/naily-$(NAILY_VERSION).gem: $(BUILD_DIR)/gems/naily-$(NAILY_VERSION).gem ; $(ACTION.COPY)
$(ISOROOT)/gems/gems/astute-$(ASTUTE_VERSION).gem: $(BUILD_DIR)/gems/astute-$(ASTUTE_VERSION).gem ; $(ACTION.COPY)

$/isoroot-eggs.done: \
		$(LOCAL_MIRROR)/eggs.done \
		$(ISOROOT)/eggs/Nailgun-$(NAILGUN_VERSION).tar.gz
	cp -r $(LOCAL_MIRROR)/eggs $(ISOROOT)/
	$(ACTION.TOUCH)

$/isoroot-gems.done: \
		$(LOCAL_MIRROR)/gems.done \
		$(BUILD_DIR)/gems/naily-$(NAILY_VERSION).gem \
		$(ISOROOT)/gems/gems/naily-$(NAILY_VERSION).gem \
		$(ISOROOT)/gems/gems/astute-$(ASTUTE_VERSION).gem
	cp -r $(LOCAL_MIRROR)/gems $(ISOROOT)/gems
	(cd $(ISOROOT)/gems && gem generate_index gems)
	$(ACTION.TOUCH)

$(ISOROOT)/puppet-nailgun.tgz: $(call find-files,puppet)
	(cd puppet && tar chzf $@ *)

$(ISOROOT)/puppet-slave.tgz: \
		$(call find-files,puppet/nailytest) \
		$(call find-files,puppet/osnailyfacter) \
		$(call find-files,fuel/deployment/puppet)
	(cd puppet && tar cf $(BUILD_DIR)/puppet-slave.tar nailytest osnailyfacter)
	(cd fuel/deployment/puppet && tar rf $(BUILD_DIR)/puppet-slave.tar ./*)
	gzip -c -9 $(BUILD_DIR)/puppet-slave.tar > $@

$/isoroot-puppetmod.done: \
		$(ISOROOT)/puppet-nailgun.tgz \
		$(ISOROOT)/puppet-slave.tgz
	$(ACTION.TOUCH)

$(ISOROOT)/ks.cfg: iso/ks.cfg ; $(ACTION.COPY)
$(ISOROOT)/bootstrap_admin_node.sh: iso/bootstrap_admin_node.sh ; $(ACTION.COPY)
$(ISOROOT)/bootstrap_admin_node.conf: iso/bootstrap_admin_node.conf ; $(ACTION.COPY)
$(ISOROOT)/.discinfo: iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: iso/.treeinfo ; $(ACTION.COPY)
$(ISOROOT)/etc/nailgun/version.yaml:
	mkdir -p $(@D)
	echo "COMMIT_SHA: `git rev-parse --verify HEAD` > $@

$/isoroot.done: \
		$/isoroot-bootstrap.done \
		$/isoroot-puppetmod.done \
		$/isoroot-eggs.done \
		$/isoroot-gems.done \
		$/isoroot-isolinux.done \
		$/isoroot-centos.done \
		$/isoroot-prepare.done
	$(ACTION.TOUCH)

# keep in mind that mkisofs touches some files inside directory
# from which it builds iso image
# that is why we need to make $/isoroot.done dependent on some files
# and then copy these files into another directory
$(ISONAME): $/isoroot.done
	rm -f $@
	mkdir -p $/isoroot-mkisofs
	rsync -a --delete $(ISOROOT)/ $/isoroot-mkisofs
	mkisofs -r -V "Mirantis Nailgun" -p "Mirantis Inc." \
		-J -T -R -b isolinux/isolinux.bin \
		-no-emul-boot \
		-boot-load-size 4 -boot-info-table \
		-x "lost+found" -o $@ $/isoroot-mkisofs
	implantisomd5 $@

# IMGSIZE is calculated as a sum of nailgun iso size plus
# installation images directory size (~165M) and syslinux directory size (~35M)
# plus a bit of free space for ext2 filesystem data
# +300M seems reasonable
IMGSIZE = $(shell echo "$(shell ls -s $(ISONAME) | awk '{print $$1}') / 1024 + 300" | bc)

$(IMGNAME): $(ISONAME)
	rm -f $/img_loop_device
	rm -f $/img_loop_partition
	rm -f $/img_loop_uuid
	sudo losetup -j $@ | awk -F: '{print $$1}' | while read loopdevice; do \
        sudo kpartx -v $$loopdevice | awk '{print "/dev/mapper/" $$1}' | while read looppartition; do \
            sudo umount -f $$looppartition; \
        done; \
        sudo kpartx -d $$loopdevice; \
        sudo losetup -d $$loopdevice; \
    done
	rm -f $@
	dd if=/dev/zero of=$@ bs=1M count=$(IMGSIZE)
	sudo losetup -f > $/img_loop_device
	sudo losetup `cat $/img_loop_device` $@
	sudo parted -s `cat $/img_loop_device` mklabel msdos
	sudo parted -s `cat $/img_loop_device` unit MB mkpart primary ext2 1 $(IMGSIZE) set 1 boot on
	sudo kpartx -a -v `cat $/img_loop_device` | awk '{print "/dev/mapper/" $$3}' > $/img_loop_partition
	sleep 1
	sudo mkfs.ext2 `cat $/img_loop_partition`
	mkdir -p $/imgroot
	sudo mount `cat $/img_loop_partition` $/imgroot
	sudo extlinux -i $/imgroot
	sudo /sbin/blkid -s UUID -o value `cat $/img_loop_partition` > $/img_loop_uuid
	sudo dd conv=notrunc bs=440 count=1 if=/usr/lib/extlinux/mbr.bin of=`cat $/img_loop_device`
	sudo cp -r $/isoroot/images $/imgroot
	sudo cp -r $/isoroot/isolinux $/imgroot
	sudo mv $/imgroot/isolinux $/imgroot/syslinux
	sudo rm $/imgroot/syslinux/isolinux.cfg
	sudo cp iso/syslinux/syslinux.cfg $/imgroot/syslinux
	sudo sed -i -e "s/will_be_substituted_with_actual_uuid/`cat $/img_loop_uuid`/g" $/imgroot/syslinux/syslinux.cfg
	sudo cp iso/ks.cfg $/imgroot/ks.cfg
	sudo sed -i -e "s/will_be_substituted_with_actual_uuid/`cat $/img_loop_uuid`/g" $/imgroot/ks.cfg
	sudo cp $(ISONAME) $/imgroot/nailgun.iso
	sudo umount -f `cat $/img_loop_partition`
	sudo kpartx -d `cat $/img_loop_device`
	sudo losetup -d `cat $/img_loop_device`
