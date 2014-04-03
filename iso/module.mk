.PHONY: iso img
all: iso img

ISOROOT:=$(BUILD_DIR)/iso/isoroot

iso: $(BUILD_DIR)/iso/iso.done
img: $(BUILD_DIR)/iso/img.done

$(BUILD_DIR)/iso/isoroot-centos.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
	mkdir -p $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/ $(ISOROOT)
	createrepo -g $(ISOROOT)/comps.xml -x 'rhel/*' \
		-u media://`head -1 $(ISOROOT)/.discinfo` $(ISOROOT)
	$(ACTION.TOUCH)

$(BUILD_DIR)/iso/isoroot-ubuntu.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
	mkdir -p $(ISOROOT)/ubuntu
	rsync -rp $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/ $(ISOROOT)/ubuntu/
	$(ACTION.TOUCH)

$(BUILD_DIR)/iso/isoroot-rhel.done: $(call depv,CACHE_RHEL)
$(BUILD_DIR)/iso/isoroot-rhel.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
ifeq ($(CACHE_RHEL),1)
	mkdir -p $(ISOROOT)/rhel
	rsync -rp $(LOCAL_MIRROR_RHEL)/ $(ISOROOT)/rhel
endif
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
	rsync -a $(BUILD_MIRROR_GEMS)/gems/ $(ISOROOT)/gems/gems
	(cd $(ISOROOT)/gems && gem generate_index gems)
	$(ACTION.TOUCH)

$(BUILD_DIR)/iso/isoroot-docker.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done
	mkdir -p $(ISOROOT)/docker
	rsync -a --delete $(LOCAL_MIRROR_DOCKER)/ $(ISOROOT)/docker
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
		$(ISOROOT)/ks.cfg \
		$(ISOROOT)/bootstrap_admin_node.sh \
		$(ISOROOT)/bootstrap_admin_node.conf \
		$(ISOROOT)/send2syslog.py \
		$(ISOROOT)/version.yaml \
		$(ISOROOT)/puppet-slave.tgz
	$(ACTION.TOUCH)

$(ISOROOT)/.discinfo: $(SOURCE_DIR)/iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: $(SOURCE_DIR)/iso/.treeinfo ; $(ACTION.COPY)
$(ISOROOT)/isolinux/isolinux.cfg: $(SOURCE_DIR)/iso/isolinux/isolinux.cfg ; $(ACTION.COPY)
$(ISOROOT)/isolinux/splash.jpg: $(SOURCE_DIR)/iso/isolinux/splash.jpg ; $(ACTION.COPY)
$(ISOROOT)/ks.cfg: $(call depv,KSYAML)
$(ISOROOT)/ks.cfg: $(SOURCE_DIR)/iso/ks.template $(SOURCE_DIR)/iso/ks.py $(KSYAML)
	python $(SOURCE_DIR)/iso/ks.py -t $(SOURCE_DIR)/iso/ks.template -c $(KSYAML) -o $@
$(ISOROOT)/bootstrap_admin_node.sh: $(SOURCE_DIR)/iso/bootstrap_admin_node.sh ; $(ACTION.COPY)
$(ISOROOT)/bootstrap_admin_node.conf: $(SOURCE_DIR)/iso/bootstrap_admin_node.conf ; $(ACTION.COPY)
$(ISOROOT)/send2syslog.py: $(BUILD_DIR)/repos/nailgun/bin/send2syslog.py ; $(ACTION.COPY)
$(BUILD_DIR)/repos/nailgun/bin/send2syslog.py: $(BUILD_DIR)/repos/nailgun.done
$(ISOROOT)/version.yaml: $(call depv,PRODUCT_VERSION)
$(ISOROOT)/version.yaml: $(BUILD_DIR)/repos/repos.done
	echo "VERSION:" > $@
	echo "  mirantis: \"$(MIRANTIS)\"" >> $@
	echo "  production: \"$(PRODUCTION)\"" >> $@
	echo "  release: \"$(PRODUCT_VERSION)\"" >> $@
ifdef BUILD_NUMBER
	echo "  build_number: \"$(BUILD_NUMBER)\"" >> $@
endif
ifdef BUILD_ID
	echo "  build_id: \"$(BUILD_ID)\"" >> $@
endif
	cat $(BUILD_DIR)/repos/version.yaml >> $@


$(ISOROOT)/puppet-slave.tgz: \
		$(BUILD_DIR)/repos/fuellib.done \
		$(call find-files,$(BUILD_DIR)/repos/fuellib/deployment/puppet)
	(cd $(BUILD_DIR)/repos/fuellib/deployment/puppet && tar rf $(ISOROOT)/puppet-slave.tar ./*)
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
		$(BUILD_DIR)/iso/isoroot-ubuntu.done \
		$(BUILD_DIR)/iso/isoroot-rhel.done \
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
	rm -f $(ISO_PATH)
	mkdir -p $(BUILD_DIR)/iso/isoroot-mkisofs
	rsync -a --delete $(ISOROOT)/ $(BUILD_DIR)/iso/isoroot-mkisofs
	sudo sed -r -i -e "s/ip=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/ip=$(MASTER_IP)/" $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	sudo sed -r -i -e "s/dns1=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/dns1=$(MASTER_DNS)/" $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	sudo sed -r -i -e "s/netmask=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/netmask=$(MASTER_NETMASK)/" $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	sudo sed -r -i -e "s/gw=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/gw=$(MASTER_GW)/" $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	sudo sed -r -i -e "s/will_be_substituted_with_PRODUCT_VERSION/$(PRODUCT_VERSION)/" $(BUILD_DIR)/iso/isoroot-mkisofs/isolinux/isolinux.cfg
	mkisofs -r -V "Mirantis Fuel" -p "Mirantis Inc." \
		-J -T -R -b isolinux/isolinux.bin \
		-no-emul-boot \
		-boot-load-size 4 -boot-info-table \
		-x "lost+found" -o $(ISO_PATH) $(BUILD_DIR)/iso/isoroot-mkisofs
	implantisomd5 $(ISO_PATH)
	$(ACTION.TOUCH)

# IMGSIZE is calculated as a sum of nailgun iso size plus
# installation images directory size (~165M) and syslinux directory size (~35M)
# plus a bit of free space for ext2 filesystem data
# +300M seems reasonable
IMGSIZE = $(shell echo "$(shell ls -s $(ISO_PATH) | awk '{print $$1}') * 1.3 / 1024" | bc)

$(BUILD_DIR)/iso/img.done: $(BUILD_DIR)/iso/iso.done
	rm -f $(BUILD_DIR)/iso/img_loop_device
	rm -f $(BUILD_DIR)/iso/img_loop_partition
	rm -f $(BUILD_DIR)/iso/img_loop_uuid
	sudo losetup -j $(IMG_PATH) | awk -F: '{print $$1}' | while read loopdevice; do \
        sudo kpartx -v $$loopdevice | awk '{print "/dev/mapper/" $$1}' | while read looppartition; do \
            sudo umount -f $$looppartition; \
        done; \
        sudo kpartx -d $$loopdevice; \
        sudo losetup -d $$loopdevice; \
    done
	rm -f $(IMG_PATH)
	dd if=/dev/zero of=$(IMG_PATH) bs=1M count=$(IMGSIZE)
	sudo losetup -f > $(BUILD_DIR)/iso/img_loop_device
	sudo losetup `cat $(BUILD_DIR)/iso/img_loop_device` $(IMG_PATH)
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
	sudo cp $(SOURCE_DIR)/iso/syslinux/syslinux.cfg $(BUILD_DIR)/iso/imgroot/syslinux  # NOTE(mihgen): Is it used for IMG file? Comments needed!
	sudo sed -i -e "s/will_be_substituted_with_actual_uuid/`cat $(BUILD_DIR)/iso/img_loop_uuid`/g" $(BUILD_DIR)/iso/imgroot/syslinux/syslinux.cfg
	sudo sed -r -i -e "s/ip=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/ip=$(MASTER_IP)/" $(BUILD_DIR)/iso/imgroot/syslinux/syslinux.cfg
	sudo sed -r -i -e "s/dns1=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/dns1=$(MASTER_DNS)/" $(BUILD_DIR)/iso/imgroot/syslinux/syslinux.cfg
	sudo sed -r -i -e "s/netmask=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/netmask=$(MASTER_NETMASK)/" $(BUILD_DIR)/iso/imgroot/syslinux/syslinux.cfg
	sudo sed -r -i -e "s/gw=[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}/gw=$(MASTER_GW)/" $(BUILD_DIR)/iso/imgroot/syslinux/syslinux.cfg
	sudo sed -r -i -e "s/will_be_substituted_with_PRODUCT_VERSION/$(PRODUCT_VERSION)/" $(BUILD_DIR)/iso/imgroot/syslinux/syslinux.cfg
	sudo cp $(BUILD_DIR)/iso/isoroot/ks.cfg $(BUILD_DIR)/iso/imgroot/ks.cfg
	sudo sed -i -e "s/will_be_substituted_with_actual_uuid/`cat $(BUILD_DIR)/iso/img_loop_uuid`/g" $(BUILD_DIR)/iso/imgroot/ks.cfg
	sudo cp $(ISO_PATH) $(BUILD_DIR)/iso/imgroot/nailgun.iso
	sudo sync
	sudo umount `cat $(BUILD_DIR)/iso/img_loop_partition`
	sudo kpartx -d `cat $(BUILD_DIR)/iso/img_loop_device`
	sudo losetup -d `cat $(BUILD_DIR)/iso/img_loop_device`
	$(ACTION.TOUCH)
