/:=$(BUILD_DIR)/iso/

.PHONY: iso
all: iso

ISOROOT:=$/isoroot

RABBITMQ_VERSION:=2.6.1
RABBITMQ_PLUGINS:=amqp_client-$(RABBITMQ_VERSION).ez rabbitmq_stomp-$(RABBITMQ_VERSION).ez
RABBITMQ_PLUGINS_URL:=http://www.rabbitmq.com/releases/plugins/v$(RABBITMQ_VERSION)

iso: $/nailgun-centos-6.3-amd64.iso

$/isoroot-centos.done: \
		$(BUILD_DIR)/rpm/rpm.done \
		$(LOCAL_MIRROR)/cache.done \
		$(ISOROOT)/repodata/comps.xml \
		$(ISOROOT)/.discinfo \
		$(ISOROOT)/.treeinfo
	mkdir -p $(ISOROOT)/Packages
	find $(CENTOS_REPO_DIR)Packages -name '*.rpm' -exec cp -n {} $(ISOROOT)/Packages \;
	find $(BUILD_DIR)/rpm/RPMS -name '*.rpm' -exec cp -n {} $(ISOROOT)/Packages \;
	createrepo -g `readlink -f "$(ISOROOT)/repodata/comps.xml"` -u media://`head -1 $(ISOROOT)/.discinfo` $(ISOROOT)
	$(ACTION.TOUCH)

$(ISOROOT)/repodata/comps.xml: $(CENTOS_REPO_DIR)/repodata/comps.xml ; $(ACTION.COPY)

$(ISOROOT)/iso/$(NETINSTALL_ISO): $(CENTOS_ISO_DIR)/$(NETINSTALL_ISO)
	@mkdir -p $(@D)
	cp $(CENTOS_ISO_DIR)/$(@F) $(@D)

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

$(addprefix $(ISOROOT)/rabbitmq-plugins/v$(RABBITMQ_VERSION)/,$(RABBITMQ_PLUGINS)):
	@mkdir -p $(@D)
	wget -O $@ $(RABBITMQ_PLUGINS_URL)/$(@F)

$/isoroot-prepare.done: \
		$(ISOROOT)/iso/$(NETINSTALL_ISO) \
		$(addprefix $(ISOROOT)/images/,$(IMAGES_FILES)) \
		$(addprefix $(ISOROOT)/EFI/BOOT/,$(EFI_FILES)) \
		$(addprefix $(ISOROOT)/rabbitmq-plugins/v$(RABBITMQ_VERSION)/,$(RABBITMQ_PLUGINS)) \
		$(addprefix $(ISOROOT)/puppet/,$(call find-files,puppet)) \
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

$(ISOROOT)/puppet/%: puppet/% ; $(ACTION.COPY)

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

$(ISOROOT)/ks.cfg: iso/ks.cfg ; $(ACTION.COPY)
$(ISOROOT)/bootstrap_admin_node.sh: iso/bootstrap_admin_node.sh ; $(ACTION.COPY)
$(ISOROOT)/.discinfo: iso/.discinfo ; $(ACTION.COPY)
$(ISOROOT)/.treeinfo: iso/.treeinfo ; $(ACTION.COPY)

$/isoroot.done: \
		$/isoroot-bootstrap.done \
		$/isoroot-eggs.done \
		$/isoroot-gems.done \
		$/isoroot-isolinux.done \
		$/isoroot-centos.done \
		$/isoroot-prepare.done
	$(ACTION.TOUCH)



$/nailgun-centos-6.3-amd64.iso: $/isoroot.done
	rm -f $@
	mkisofs -r -V "Mirantis Nailgun" -p "Mirantis" \
		-J -T -R -b isolinux/isolinux.bin \
		-no-emul-boot \
		-boot-load-size 8 -boot-info-table \
		-x "lost+found" -o $@ $(ISOROOT)
	implantisomd5 $/nailgun-centos-6.3-amd64.iso
