/:=$(BUILD_DIR)/iso/

CENTOS_63_RELEASE:=6.3
CENTOS_63_ARCH:=x86_64
CENTOS_63_MIRROR:=http://mirror.yandex.ru/centos/$(CENTOS_63_RELEASE)/os/$(CENTOS_63_ARCH)
CENTOS_63_NETINSTALL:=http://mirror.yandex.ru/centos/$(CENTOS_63_RELEASE)/isos/$(CENTOS_63_ARCH)
CENTOS_63_GPG:=http://mirror.yandex.ru/centos

.PHONY: iso
all: iso

ISOROOT:=$/isoroot
ISOLINUX_FILES:=boot.msg grub.conf initrd.img isolinux.bin memtest splash.jpg vesamenu.c32 vmlinuz
IMAGES_FILES:=efiboot.img efidisk.img install.img
EFI_FILES:=BOOTX64.conf BOOTX64.efi splash.xpm.gz
BOOTSTRAP_FILES:=initramfs.img linux
GPGFILES:=RPM-GPG-KEY-CentOS-6 RPM-GPG-KEY-CentOS-Debug-6 RPM-GPG-KEY-CentOS-Security-6 RPM-GPG-KEY-CentOS-Testing-6
NETINSTALL_ISO:=CentOS-6.3-x86_64-netinstall-EFI.iso

RABBITMQ_VERSION:=2.6.1
RABBITMQ_PLUGINS:=amqp_client-$(RABBITMQ_VERSION).ez rabbitmq_stomp-$(RABBITMQ_VERSION).ez
RABBITMQ_PLUGINS_URL:=http://www.rabbitmq.com/releases/plugins/v$(RABBITMQ_VERSION)

NAILGUN_VERSION:=0.1.0

iso: $/nailgun-centos-6.3-amd64.iso

$/isoroot-centos.done: \
		$(BUILD_DIR)/packages/rpm/rpm.done \
		$(centos.packages)/cache.done \
		$(ISOROOT)/repodata/comps.xml \
		$(ISOROOT)/.discinfo \
		$(ISOROOT)/.treeinfo
	mkdir -p $(ISOROOT)/Packages
	find $(centos.packages)/Packages -name '*.rpm' -exec cp -n {} $(ISOROOT)/Packages \;
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -n {} $(ISOROOT)/Packages \;
	createrepo -g `readlink -f "$(ISOROOT)/repodata/comps.xml"` -u media://`head -1 $(ISOROOT)/.discinfo` $(ISOROOT)
	$(ACTION.TOUCH)

$(ISOROOT)/repodata/comps.xml: $(CENTOS_REPO_DIR)comps.xml ; $(ACTION.COPY)

$(addprefix $(ISOROOT)/isolinux/,$(ISOLINUX_FILES)):
	@mkdir -p $(@D)
	wget -O $@ $(CENTOS_63_MIRROR)/isolinux/$(@F)

$(ISOROOT)/isolinux/isolinux.cfg: iso/isolinux/isolinux.cfg ; $(ACTION.COPY)

$(ISOROOT)/netinstall/centos.iso:
	@mkdir -p $(@D)
	wget -O $@ $(CENTOS_63_NETINSTALL)/$(NETINSTALL_ISO)

$/isoroot-isolinux.done: \
		$(addprefix $(ISOROOT)/isolinux/,$(ISOLINUX_FILES)) \
		$(ISOROOT)/isolinux/isolinux.cfg \
	$(ACTION.TOUCH)

$(addprefix $(ISOROOT)/images/,$(IMAGES_FILES)):
	@mkdir -p $(@D)
	wget -O $@ $(CENTOS_63_MIRROR)/images/$(@F)

$(addprefix $(ISOROOT)/EFI/BOOT/,$(EFI_FILES)):
	@mkdir -p $(@D)
	wget -O $@ $(CENTOS_63_MIRROR)/EFI/BOOT/$(@F)

$(addprefix $(ISOROOT)/rabbitmq-plugins/,$(RABBITMQ_PLUGINS)):
	@mkdir -p $(@D)
	wget -O $@ $(RABBITMQ_PLUGINS_URL)/$(@F)

$/isoroot-prepare.done:\
		$(ISOROOT)/netinstall/centos.iso \
		$(addprefix $(ISOROOT)/images/,$(IMAGES_FILES)) \
		$(addprefix $(ISOROOT)/EFI/BOOT/,$(EFI_FILES)) \
		$(addprefix $(ISOROOT)/,$(GPGFILES)) \
		$(addprefix $(ISOROOT)/rabbitmq-plugins/,$(RABBITMQ_PLUGINS)) \
	$(ACTION.TOUCH)

$(addprefix $(ISOROOT)/,$(GPGFILES)):
	wget -O $@ $(CENTOS_63_GPG)/$(@F)

$/isoroot-bootstrap.done: \
		$(ISOROOT)/bootstrap/bootstrap.rsa \
		$(addprefix $(ISOROOT)/bootstrap/, $(BOOTSTRAP_FILES))
	$(ACTION.TOUCH)

$(addprefix $(ISOROOT)/bootstrap/, $(BOOTSTRAP_FILES)): \
		bootstrap
	@mkdir -p $(@D)
	cp $(BUILD_DIR)/bootstrap/$(@F) $@

$(ISOROOT)/bootstrap/bootstrap.rsa: bootstrap/ssh/id_rsa ; $(ACTION.COPY)

$(ISOROOT)/eggs/Nailgun-$(NAILGUN_VERSION).tar.gz: \
		sdist-nailgun
	@mkdir -p $(@D)
	cp $(BUILD_DIR)/nailgun/$(@F) $@

$(ISOROOT)/puppet/%: puppet/% ; $(ACTION.COPY)

$(ISOROOT)/eggs/%: $(LOCAL_MIRROR)/eggs/% ; $(ACTION.COPY)
$(ISOROOT)/gems/gems/%: $(LOCAL_MIRROR)/gems/% ; $(ACTION.COPY)

$/isoroot-eggs.done: \
		$(CENTOS_REPO_DIR)eggs-gems.done \
		$(addprefix $(ISOROOT)/eggs/,$(call find-files,$(LOCAL_MIRROR)/eggs)) \
		$(ISOROOT)/eggs/Nailgun-$(NAILGUN_VERSION).tar.gz
	$(ACTION.TOUCH)

$/isoroot-gems.done: \
		$(CENTOS_REPO_DIR)eggs-gems.done \
		$(addprefix $(ISOROOT)/gems/gems/,$(call find-files,$(LOCAL_MIRROR)/gems))
	$(ACTION.TOUCH)

$/isoroot.done: \
		$/isoroot-centos.done \
		$/isoroot-prepare.done \
		$/isoroot-isolinux.done \
		$(ISOROOT)/ks.cfg \
		$/isoroot-bootstrap.done \
		$(ISOROOT)/bootstrap_admin_node.sh \
		$/isoroot-eggs.done \
		$/isoroot-gems.done \
		$(addprefix $(ISOROOT)/sync/,$(call find-files,iso/sync)) \
		$(addprefix $(ISOROOT)/puppet/,$(call find-files,puppet))
	$(ACTION.TOUCH)

$(ISOROOT)/sync/%: iso/sync/% ; $(ACTION.COPY)

$(ISOROOT)/ks.cfg: iso/ks.cfg ; $(ACTION.COPY)
$(ISOROOT)/bootstrap_admin_node.sh: iso/bootstrap_admin_node.sh ; $(ACTION.COPY)
$(ISOROOT)/.discinfo: iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: iso/.treeinfo ; $(ACTION.COPY)

$/nailgun-centos-6.3-amd64.iso: $/isoroot.done
	rm -f $@
	mkisofs -r -V "Mirantis Nailgun" -p "Mirantis" \
		-J -T -R -b isolinux/isolinux.bin \
		-no-emul-boot \
		-boot-load-size 8 -boot-info-table \
		-x "lost+found" -o $@ $(ISOROOT)
	implantisomd5 $/nailgun-centos-6.3-amd64.iso
