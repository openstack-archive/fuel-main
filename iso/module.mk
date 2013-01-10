/:=$(BUILD_DIR)/iso/

.PHONY: iso
all: iso

ISOROOT:=$/isoroot

iso: $/nailgun-centos-6.3-amd64.iso
img: $/nailgun-centos-6.3-amd64.img

$/isoroot-centos.done: \
		$(BUILD_DIR)/rpm/rpm.done \
		$(LOCAL_MIRROR)/cache.done \
		$(ISOROOT)/repodata/comps.xml \
		$(ISOROOT)/.discinfo \
		$(ISOROOT)/.treeinfo
	mkdir -p $(ISOROOT)/Packages
	find $(CENTOS_REPO_DIR)Packages -name '*.rpm' -exec cp -u {} $(ISOROOT)/Packages \;
	createrepo -x 'more_rpm/*' -g `readlink -f "$(ISOROOT)/repodata/comps.xml"` -u media://`head -1 $(ISOROOT)/.discinfo` $(ISOROOT)
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
		$(ISOROOT)/bootstrap_admin_node.sh
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

FUEL_PACKAGES=http://download.mirantis.com/epel-fuel/x86_64
$/isoroot-puppetmod.done: \
		$(ISOROOT)/puppet-nailgun.tgz \
		$(ISOROOT)/puppet-slave.tgz
	mkdir -p $(ISOROOT)/more_rpm
	cd $(ISOROOT)/more_rpm && wget -c \
		$(FUEL_PACKAGES)/MySQL-shared-5.5.28-1.el6.x86_64.rpm \
		$(FUEL_PACKAGES)/MySQL-client-5.5.28-1.el6.x86_64.rpm \
		$(FUEL_PACKAGES)/MySQL-server-5.5.28_wsrep_23.7-1.rhel5.x86_64.rpm \
		$(FUEL_PACKAGES)/galera-23.2.2-1.rhel5.x86_64.rpm
	$(ACTION.TOUCH)

$(ISOROOT)/ks.cfg: iso/ks.cfg ; $(ACTION.COPY)
$(ISOROOT)/bootstrap_admin_node.sh: iso/bootstrap_admin_node.sh ; $(ACTION.COPY)
$(ISOROOT)/.discinfo: iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: iso/.treeinfo ; $(ACTION.COPY)

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
$/nailgun-centos-6.3-amd64.iso: $/isoroot.done
	rm -f $@
	mkdir -p $/isoroot-mkisofs
	rsync -a --delete $(ISOROOT)/ $/isoroot-mkisofs
	mkisofs -r -V "Mirantis Nailgun" -p "Mirantis Inc." \
		-J -T -R -b isolinux/isolinux.bin \
		-no-emul-boot \
		-boot-load-size 4 -boot-info-table \
		-x "lost+found" -o $@ $/isoroot-mkisofs
	implantisomd5 $@

$/nailgun-centos-6.3-amd64.img: $/nailgun-centos-6.3-amd64.iso
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
	dd if=/dev/zero of=$/nailgun-centos-6.3-amd64.img bs=1M count=2048
	sudo losetup -f > $/img_loop_device
	sudo losetup `cat $/img_loop_device` $@
	sudo wipefs -a `cat $/img_loop_device`
	sudo parted -s `cat $/img_loop_device` mklabel msdos
	sudo parted -s `cat $/img_loop_device` unit MB mkpart primary ext2 1 2048 set 1 boot on
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
	sudo cp $/nailgun-centos-6.3-amd64.iso $/imgroot/nailgun.iso
	sudo umount -f `cat $/img_loop_partition`
	sudo kpartx -d `cat $/img_loop_device`
	sudo losetup -d `cat $/img_loop_device`