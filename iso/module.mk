.PHONY: all iso img version-yaml centos-repo ubuntu-repo
.DELETE_ON_ERROR: $(ISO_PATH) $(IMG_PATH)

all: iso img version-yaml

ISOROOT:=$(BUILD_DIR)/iso/isoroot

iso: $(ISO_PATH)
img: $(IMG_PATH)

########################
# VERSION-YAML ARTIFACT
########################
version-yaml: $(ARTS_DIR)/$(VERSION_YAML_ART_NAME)

$(ARTS_DIR)/$(VERSION_YAML_ART_NAME): $(ISOROOT)/$(VERSION_YAML_ART_NAME)
	$(ACTION.COPY)

$(ISOROOT)/$(VERSION_YAML_ART_NAME): $(call depv,PRODUCT_VERSION)
$(ISOROOT)/$(VERSION_YAML_ART_NAME): $(call depv,FEATURE_GROUPS)
$(ISOROOT)/$(VERSION_YAML_ART_NAME): $(BUILD_DIR)/repos/repos.done \
		$(ISOROOT)/openstack_version
	mkdir -p $(@D)
	echo "VERSION:" > $@
	echo "  feature_groups:" >> $@
	$(foreach group,$(FEATURE_GROUPS),echo "    - $(group)" >> $@;)
	echo "  production: \"$(PRODUCTION)\"" >> $@
	echo "  release: \"$(PRODUCT_VERSION)\"" >> $@
	echo -n "  openstack_version: \"" >> $@
	cat $(ISOROOT)/openstack_version | tr -d '\n' >> $@
	echo "\"" >> $@
	echo "  api: \"1.0\"" >> $@
ifdef BUILD_NUMBER
	echo "  build_number: \"$(BUILD_NUMBER)\"" >> $@
endif
ifdef BUILD_ID
	echo "  build_id: \"$(BUILD_ID)\"" >> $@
endif
	cat $(BUILD_DIR)/repos/version.yaml >> $@

########################
# CENTOS MIRROR ARTIFACT
########################
centos-repo: $(ARTS_DIR)/$(CENTOS_REPO_ART_NAME)

$(ARTS_DIR)/$(CENTOS_REPO_ART_NAME): $(BUILD_DIR)/iso/isoroot-centos.done
	mkdir -p $(@D)
	tar cf $@ -C $(ISOROOT) --xform s:^:centos-repo/: comps.xml  EFI  images  isolinux  Packages  repodata centos-versions.yaml

CENTOS_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(CENTOS_REPO_ART_NAME))

ifdef CENTOS_DEP_FILE
$(BUILD_DIR)/iso/isoroot-centos.done: \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
	mkdir -p $(ISOROOT)
	tar xf $(CENTOS_DEP_FILE) -C $(ISOROOT) --xform s:^centos-repo/::
	createrepo -g $(ISOROOT)/comps.xml \
		-u media://`head -1 $(ISOROOT)/.discinfo` $(ISOROOT)
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/iso/isoroot-centos.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/mirror/make-changelog.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/packages/build-late.done \
		$(BUILD_DIR)/openstack/build.done \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done \
		$(BUILD_DIR)/packages/rpm/fuel-docker-images.done
	mkdir -p $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/ $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR)/centos-packages.changelog $(ISOROOT)
	createrepo -g $(ISOROOT)/comps.xml \
		-u media://`head -1 $(ISOROOT)/.discinfo` $(ISOROOT)
	rpm -qi -p $(ISOROOT)/Packages/*.rpm | $(SOURCE_DIR)/iso/pkg-versions.awk > $(ISOROOT)/centos-versions.yaml
	$(ACTION.TOUCH)
endif

########################
# UBUNTU MIRROR ARTIFACT
########################
ubuntu-repo: $(ARTS_DIR)/$(UBUNTU_REPO_ART_NAME)

$(ARTS_DIR)/$(UBUNTU_REPO_ART_NAME): $(BUILD_DIR)/iso/isoroot-ubuntu.done
	mkdir -p $(@D)
	tar cf $@ -C $(ISOROOT)/ubuntu --xform s:^./:ubuntu-repo/: .

UBUNTU_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(UBUNTU_REPO_ART_NAME))

ifdef UBUNTU_DEP_FILE
$(BUILD_DIR)/iso/isoroot-ubuntu.done: \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
	mkdir -p $(ISOROOT)/ubuntu
	tar xf $(UBUNTU_DEP_FILE) -C $(ISOROOT)/ubuntu --xform s:^ubuntu-repo/::
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/iso/isoroot-ubuntu.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/mirror/make-changelog.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
	mkdir -p $(ISOROOT)/ubuntu
	rsync -rp $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/ $(ISOROOT)/ubuntu/
	rsync -rp $(LOCAL_MIRROR)/ubuntu-packages.changelog $(ISOROOT)
	zcat $(ISOROOT)/ubuntu/dists/$(PRODUCT_NAME)$(PRODUCT_VERSION)/main/binary-amd64/Packages.gz | $(SOURCE_DIR)/iso/pkg-versions.awk > $(ISOROOT)/ubuntu/ubuntu-versions.yaml
	$(ACTION.TOUCH)
endif

########################
# PUPPET
########################
# PUPPET_ART_NAME is defined in /puppet/module.mk
# we need to repack puppet artifact because artifact
# has puppet directory packed into it but we need to have an
# archive of puppet modules packed into it
#$(ISOROOT)/puppet-slave.tgz: $(BUILD_DIR)/puppet/$(PUPPET_ART_NAME)
#	tar zxf $(BUILD_DIR)/puppet/$(PUPPET_ART_NAME) -C $(BUILD_DIR)/iso
#	tar zcf $(ISOROOT)/puppet-slave.tgz -C $(BUILD_DIR)/iso/puppet .

########################
# DOCKER
########################
# DOCKER_ART_NAME is defined in /docker/module.mk
$(ISOROOT)/docker.done: $(BUILD_DIR)/docker/build.done \
		$(BUILD_DIR)/packages/rpm/fuel-docker-images.done
	$(ACTION.TOUCH)

########################
# Extra files
########################

$(BUILD_DIR)/iso/isoroot-dotfiles.done: \
		$(ISOROOT)/.discinfo \
		$(ISOROOT)/.treeinfo
	$(ACTION.TOUCH)

$(ISOROOT)/openstack_version: $(BUILD_DIR)/upgrade/$(OPENSTACK_YAML_ART_NAME)
	python -c "import yaml; print filter(lambda r: r['fields'].get('name'), yaml.load(open('$(BUILD_DIR)/upgrade/$(OPENSTACK_YAML_ART_NAME)')))[0]['fields']['version']" > $@

$(BUILD_DIR)/iso/isoroot-files.done: \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done \
		$(ISOROOT)/isolinux/isolinux.cfg \
		$(ISOROOT)/isolinux/splash.jpg \
		$(ISOROOT)/ks.cfg \
		$(ISOROOT)/bootstrap_admin_node.sh \
		$(ISOROOT)/bootstrap_admin_node.conf \
		$(ISOROOT)/send2syslog.py \
		$(ISOROOT)/version.yaml \
		$(ISOROOT)/openstack_version \
		$(ISOROOT)/centos-versions.yaml \
		$(ISOROOT)/ubuntu-versions.yaml 
	$(ACTION.TOUCH)

$(ISOROOT)/.discinfo: $(SOURCE_DIR)/iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: $(SOURCE_DIR)/iso/.treeinfo ; $(ACTION.COPY)
$(ISOROOT)/isolinux/isolinux.cfg: $(SOURCE_DIR)/iso/isolinux/isolinux.cfg ; $(ACTION.COPY)
$(ISOROOT)/isolinux/splash.jpg: $(call depv,FEATURE_GROUPS)
ifeq ($(filter mirantis,$(FEATURE_GROUPS)),mirantis)
$(ISOROOT)/isolinux/splash.jpg: $(SOURCE_DIR)/iso/isolinux/splash.jpg ; $(ACTION.COPY)
else
$(ISOROOT)/isolinux/splash.jpg: $(SOURCE_DIR)/iso/isolinux/splash_community.jpg ; $(ACTION.COPY)
endif
$(ISOROOT)/ks.cfg: $(call depv,KSYAML)
$(ISOROOT)/ks.cfg: $(SOURCE_DIR)/iso/ks.template $(SOURCE_DIR)/iso/ks.py $(KSYAML)
	python $(SOURCE_DIR)/iso/ks.py -t $(SOURCE_DIR)/iso/ks.template -c $(KSYAML) -o $@
ifeq ($(PRODUCTION),docker)
$(ISOROOT)/bootstrap_admin_node.sh: $(SOURCE_DIR)/iso/bootstrap_admin_node.docker.sh ; $(ACTION.COPY)
else
$(ISOROOT)/bootstrap_admin_node.sh: $(SOURCE_DIR)/iso/bootstrap_admin_node.sh ; $(ACTION.COPY)
endif
$(ISOROOT)/bootstrap_admin_node.conf: $(SOURCE_DIR)/iso/bootstrap_admin_node.conf ; $(ACTION.COPY)
$(ISOROOT)/send2syslog.py: $(BUILD_DIR)/repos/nailgun/bin/send2syslog.py ; $(ACTION.COPY)
$(BUILD_DIR)/repos/nailgun/bin/send2syslog.py: $(BUILD_DIR)/repos/nailgun.done

$(ISOROOT)/centos-versions.yaml: $(BUILD_DIR)/iso/isoroot-centos.done
#	here we don't need to do anything because we unpack centos repo in $(ISOROOT) and it already contains centos-versions.yaml
	$(ACTION.TOUCH)

$(ISOROOT)/ubuntu-versions.yaml: $(BUILD_DIR)/iso/isoroot-ubuntu.done
	cp $(ISOROOT)/ubuntu/ubuntu-versions.yaml $@
	$(ACTION.TOUCH)

ifeq ($(PRODUCTION),docker)
$(BUILD_DIR)/iso/isoroot.done: $(ISOROOT)/docker.done
endif

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

ifeq ($(filter mirantis,$(FEATURE_GROUPS)),mirantis)
ISO_VOLUME_ID:="Mirantis_Fuel"
ISO_VOLUME_PREP:="Mirantis Inc."
else
ISO_VOLUME_ID:="OpenStack_Fuel"
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
	mkisofs -r -V $(ISO_VOLUME_ID) -p $(ISO_VOLUME_PREP) \
		-J -T -R -b isolinux/isolinux.bin \
		-no-emul-boot \
		-boot-load-size 4 -boot-info-table \
		-x "lost+found" -o $@ $(BUILD_DIR)/iso/isoroot-mkisofs
	isohybrid $@
	implantisomd5 $@

# IMGSIZE is calculated as a sum of iso size plus
# installation images directory size (~165M) and syslinux directory size (~35M)
# plus a bit of free space for ext2 filesystem data
# +300M seems reasonable
IMGSIZE = $(shell echo "$(shell ls -s $(ISO_PATH) | awk '{print $$1}') * 1.3 / 1024" | bc)

$(IMG_PATH): $(ISO_PATH)
	rm -f $(BUILD_DIR)/iso/img_loop_device
	rm -f $(BUILD_DIR)/iso/img_loop_partition
	rm -f $(BUILD_DIR)/iso/img_loop_uuid
	mkdir -p $(@D)
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
