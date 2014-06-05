.PHONY: upgrade fuel-upgrade openstack-upgrade

upgrade: $(BUILD_DIR)/upgrade/upgrade.done

fuel-upgrade: $(BUILD_DIR)/upgrade/fuel.done

openstack-upgrade: $(BUILD_DIR)/upgrade/openstack.done

$(BUILD_DIR)/upgrade/upgrade.done: \
		$(BUILD_DIR)/upgrade/openstack-part.done \
		$(BUILD_DIR)/upgrade/fuel-part.done \
		$(BUILD_DIR)/upgrade/common-part.done
	rm -f $(BUILD_DIR)/upgrade/fuel-$(PRODUCT_VERSION)-upgrade.tar
	tar Af $(BUILD_DIR)/upgrade/fuel-$(PRODUCT_VERSION)-upgrade.tar \
		$(BUILD_DIR)/upgrade/fuel-part.tar
	tar Af $(BUILD_DIR)/upgrade/fuel-$(PRODUCT_VERSION)-upgrade.tar \
		$(BUILD_DIR)/upgrade/openstack-part.tar
	tar Af $(BUILD_DIR)/upgrade/fuel-$(PRODUCT_VERSION)-upgrade.tar \
		$(BUILD_DIR)/upgrade/common-part.tar
	# Looks like gzip is useless here
	# gzip $(BUILD_DIR)/upgrade/fuel-$(PRODUCT_VERSION)-upgrade.tar
	$(ACTION.TOUCH)

$(BUILD_DIR)/upgrade/common-part.done: \
		$(BUILD_DIR)/iso/iso.done
	rm -f $(BUILD_DIR)/upgrade/common-part.tar
	mkdir -p $(BUILD_DIR)/upgrade/venv
	tar cf $(BUILD_DIR)/upgrade/common-part.tar -C $(BUILD_DIR)/repos/fuellib/deployment --xform s:^:upgrade/: puppet
	# Requires virtualenv, pip, python-dev packages
	virtualenv $(BUILD_DIR)/upgrade/venv
	$(BUILD_DIR)/upgrade/venv/bin/pip install $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade
	$(BUILD_DIR)/upgrade/venv/bin/pip install -r $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade/requirements.txt
	tar rf $(BUILD_DIR)/upgrade/common-part.tar -C $(BUILD_DIR)/upgrade/venv/lib/python* --xform s:^:upgrade/: site-packages
	tar rf $(BUILD_DIR)/upgrade/common-part.tar -C $(BUILD_DIR)/upgrade/venv --xform s:^:upgrade/: bin/fuel-upgrade
	tar rf $(BUILD_DIR)/upgrade/common-part.tar --mode=755 -C $(SOURCE_DIR)/upgrade upgrade.sh
	$(ACTION.TOUCH)

$(BUILD_DIR)/upgrade/fuel-part.done: \
		$(BUILD_DIR)/iso/iso.done
	mkdir -p $(BUILD_DIR)/upgrade
	rm -f $(BUILD_DIR)/upgrade/fuel-part.tar
	tar cf $(BUILD_DIR)/upgrade/fuel-part.tar -C $(ISOROOT)/docker/images --xform s:^:upgrade/images/: fuel-images.tar.lrz
	tar rf $(BUILD_DIR)/upgrade/fuel-part.tar -C $(BUILD_DIR)/iso/isoroot --xform s:^:upgrade/config/: version.yaml
	$(ACTION.TOUCH)

$(BUILD_DIR)/upgrade/openstack-part.done: \
		$(BUILD_DIR)/iso/iso.done
	mkdir -p $(BUILD_DIR)/upgrade
	rm -f $(BUILD_DIR)/upgrade/openstack-part.tar
	tar cf $(BUILD_DIR)/upgrade/openstack-part.tar -C $(LOCAL_MIRROR) --xform s:^:upgrade/repos/: centos ubuntu
	tar rf $(BUILD_DIR)/upgrade/openstack-part.tar -C $(BUILD_DIR)/repos/nailgun/nailgun/nailgun/fixtures --xform s:^:upgrade/config/: openstack.yaml
	$(ACTION.TOUCH)

$(BUILD_DIR)/upgrade/fuel.done: \
		$(BUILD_DIR)/upgrade/common-part.done \
		$(BUILD_DIR)/upgrade/fuel-part.done
	rm -f $(BUILD_DIR)/upgrade/master-upgrade-$(PRODUCT_VERSION).tar
	tar Af $(BUILD_DIR)/upgrade/master-upgrade-$(PRODUCT_VERSION).tar $(BUILD_DIR)/upgrade/fuel-part.tar
	tar Af $(BUILD_DIR)/upgrade/master-upgrade-$(PRODUCT_VERSION).tar $(BUILD_DIR)/upgrade/common-part.tar
	$(ACTION.TOUCH)

$(BUILD_DIR)/upgrade/openstack.done: \
		$(BUILD_DIR)/upgrade/common-part.done \
		$(BUILD_DIR)/upgrade/openstack-part.done
	rm -f $(BUILD_DIR)/upgrade/openstack-upgrade-$(PRODUCT_VERSION).tar
	tar Af $(BUILD_DIR)/upgrade/openstack-upgrade-$(PRODUCT_VERSION).tar $(BUILD_DIR)/upgrade/openstack-part.tar
	tar Af $(BUILD_DIR)/upgrade/openstack-upgrade-$(PRODUCT_VERSION).tar $(BUILD_DIR)/upgrade/common-part.tar
	$(ACTION.TOUCH)
