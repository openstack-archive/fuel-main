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
	cd $(BUILD_DIR)/repos/fuellib/deployment && tar cf $(BUILD_DIR)/upgrade/common-part.tar puppet
	# Requires virtualenv, pip, python-dev packages
	virtualenv $(BUILD_DIR)/upgrade/venv
	$(BUILD_DIR)/upgrade/venv/bin/pip install $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade
	$(BUILD_DIR)/upgrade/venv/bin/pip install -r $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade/requirements.txt
	cd $(BUILD_DIR)/upgrade/venv/lib/python* && tar rf $(BUILD_DIR)/upgrade/common-part.tar site-packages
	cd $(BUILD_DIR)/upgrade/venv && tar rf $(BUILD_DIR)/upgrade/common-part.tar bin/fuel-upgrade
	cd $(SOURCE_DIR)/upgrade && tar rf $(BUILD_DIR)/upgrade/common-part.tar upgrade.sh
	$(ACTION.TOUCH)

$(BUILD_DIR)/upgrade/fuel-part.done: \
		$(BUILD_DIR)/iso/iso.done
	mkdir -p $(BUILD_DIR)/upgrade
	rm -f $(BUILD_DIR)/upgrade/fuel-part.tar
	cd $(ISOROOT)/docker/images/ && tar cf $(BUILD_DIR)/upgrade/fuel-part.tar fuel-images.tar.lrz
	cd $(BUILD_DIR)/iso/isoroot && tar rf $(BUILD_DIR)/upgrade/fuel-part.tar version.yaml
	$(ACTION.TOUCH)

$(BUILD_DIR)/upgrade/openstack-part.done: \
		$(BUILD_DIR)/iso/iso.done
	mkdir -p $(BUILD_DIR)/upgrade
	rm -f $(BUILD_DIR)/upgrade/openstack-part.tar
	cd $(LOCAL_MIRROR) && tar cf $(BUILD_DIR)/upgrade/openstack-part.tar centos ubuntu
	cd $(BUILD_DIR)/repos/nailgun/nailgun/nailgun/fixtures && tar rf $(BUILD_DIR)/upgrade/openstack-part.tar openstack.yaml
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
