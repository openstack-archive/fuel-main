.PHONY: all iso version-yaml centos-repo ubuntu-repo
.DELETE_ON_ERROR: $(ISO_PATH)

all: iso version-yaml openstack-yaml

ISOROOT:=$(BUILD_DIR)/iso/isoroot

iso: $(ISO_PATH)

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
	tar cf $@ -C $(ISOROOT) --xform s:^:centos-repo/: comps.xml  EFI  images  isolinux  Packages  repodata

CENTOS_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(CENTOS_REPO_ART_NAME))

ifdef CENTOS_DEP_FILE
$(BUILD_DIR)/iso/isoroot-centos.done: \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
	mkdir -p $(ISOROOT)
	tar xf $(CENTOS_DEP_FILE) -C $(ISOROOT) --xform s:^centos-repo/::
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/iso/isoroot-centos.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/mirror/make-changelog.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/packages/build-late.done \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done
	mkdir -p $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/ $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR_MOS_CENTOS) $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR)/extra-repos $(ISOROOT)
	rsync -rp $(LOCAL_MIRROR)/centos-packages.changelog $(ISOROOT)
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

$(ISOROOT)/openstack_version: $(BUILD_DIR)/iso/$(OPENSTACK_YAML_ART_NAME)
	mkdir -p $(@D)
	python -c "import yaml; print filter(lambda r: r['fields'].get('name'), yaml.load(open('$(BUILD_DIR)/iso/$(OPENSTACK_YAML_ART_NAME)')))[0]['fields']['version']" > $@


openstack-yaml: $(ARTS_DIR)/$(OPENSTACK_YAML_ART_NAME)

$(ARTS_DIR)/$(OPENSTACK_YAML_ART_NAME): $(BUILD_DIR)/iso/$(OPENSTACK_YAML_ART_NAME)
	$(ACTION.COPY)

$(BUILD_DIR)/iso/$(OPENSTACK_YAML_ART_NAME): $(BUILD_DIR)/repos/fuel-nailgun.done
	mkdir -p $(@D)
	cp $(BUILD_DIR)/repos/fuel-nailgun/nailgun/nailgun/fixtures/openstack.yaml $@


$(BUILD_DIR)/iso/isoroot-files.done: \
		$(BUILD_DIR)/iso/isoroot-dotfiles.done \
		$(ISOROOT)/isolinux/isolinux.cfg \
		$(ISOROOT)/isolinux/splash.jpg \
		$(ISOROOT)/ks.cfg \
		$(ISOROOT)/bootstrap_admin_node.sh \
		$(ISOROOT)/bootstrap_admin_node.conf \
		$(ISOROOT)/send2syslog.py \
		$(ISOROOT)/version.yaml \
		$(ISOROOT)/openstack_version
	$(ACTION.TOUCH)

$(ISOROOT)/.discinfo: $(SOURCE_DIR)/iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: $(SOURCE_DIR)/iso/.treeinfo ; $(ACTION.COPY)

# It's a callable object.
# Usage: $(call create_ks_repo_entry,repo)
# where:
# repo=repo_name,http://path_to_the_repo,repo_priority
# repo_priority is a number from 1 to 99
define create_ks_repo_entry
repo --name="$(call get_repo_name,$1)" --baseurl=file:///mnt/source/extra-repos/$(call get_repo_name,$1) --cost=$(call get_repo_priority,$1)
endef

$(ISOROOT)/ks.yaml: \
	export ks_contents:=$(foreach repo,$(EXTRA_RPM_REPOS),\n$(space)$(call create_ks_repo_entry,$(repo))\n)
$(ISOROOT)/ks.yaml:
	@mkdir -p $(@D)
	cp $(KSYAML) $@
ifneq ($(strip $(EXTRA_RPM_REPOS)),)
	/bin/echo "extra_repos:" >> $@
	/bin/echo -e "$${ks_contents}" >> $@
endif

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

$(ISOROOT)/bootstrap_admin_node.sh: $(SOURCE_DIR)/iso/bootstrap_admin_node.sh ; $(ACTION.COPY)
$(ISOROOT)/bootstrap_admin_node.conf: $(SOURCE_DIR)/iso/bootstrap_admin_node.conf ; $(ACTION.COPY)
$(ISOROOT)/send2syslog.py: $(BUILD_DIR)/repos/fuel-nailgun/bin/send2syslog.py ; $(ACTION.COPY)
$(BUILD_DIR)/repos/fuel-nailgun/bin/send2syslog.py: $(BUILD_DIR)/repos/fuel-nailgun.done

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
