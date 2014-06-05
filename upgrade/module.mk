.PHONY: upgrade fuel-upgrade openstack-upgrade

upgrade: $(BUILD_DIR)/upgrade/upgrade.done

fuel-upgrade: $(BUILD_DIR)/upgrade/fuel.done

openstack-upgrade: $(BUILD_DIR)/upgrade/openstack.done

$(BUILD_DIR)/upgrade/upgrade.done: \
		$(BUILD_DIR)/upgrade/openstack-part.done
		$(BUILD_DIR)/upgrade/fuel-part.done
		$(BUILD_DIR)/upgrade/common.done
	tar zcf $(BUILD_DIR)/upgrade/fuel-$(PRODUCT_VERSION)-upgrade.tar.gz \
		@$(BUILD_DIR)/upgrade/fuel-part.tar.gz \
		@$(BUILD_DIR)/upgrade/openstack-part.tar.gz \
		@$(BUILD_DIR)/upgrade/common-part.tar

$(BUILD_DIR)/upgrade/common-part.done: \
		$(BUILD_DIR)/iso/iso.done
	mkdir -p $(BUILD_DIR)/upgrade/venv
	cd $(BUILD_DIR)/repos/fuellib/deployment && tar cf $(BUILD_DIR)/upgrade/common-part.tar puppet
	virtualenv $(BUILD_DIR)/upgrade/venv
	$(BUILD_DIR)/upgrade/venv/bin/pip install $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade
	$(BUILD_DIR)/upgrade/venv/bin/pip install -r $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade/requirements.txt
	cd $(BUILD_DIR)/upgrade/venv/lib/python* && tar rf $(BUILD_DIR)/upgrade/common-part.tar site-packages
	cd $(BUILD_DIR)/upgrade/venv && tar rf $(BUILD_DIR)/upgrade/common-part.tar bin/fuel-upgrade
	cd $(SOURCE_DIR)/upgrade && tar rf $(BUILD_DIR)/upgrade/common-part.tar upgrade.sh

$(BUILD_DIR)/upgrade/fuel-part.done: \
		$(BUILD_DIR)/iso/iso.done
	mkdir -p $(BUILD_DIR)/upgrade
	cd $(ISO_ROOT)/docker/images/ && tar cf $(BUILD_DIR)/upgrade/fuel-part.tar fuel-images.tar.lrz
	cd $(BUILD_DIR)/iso/isoroot && tar rf $(BUILD_DIR)/upgrade/fuel-part.tar version.yaml

$(BUILD_DIR)/upgrade/openstack-part.done: \
		$(BUILD_DIR)/iso/iso.done
	mkdir -p $(BUILD_DIR)/upgrade
	cd $(LOCAL_MIRROR) && tar cf $(BUILD_DIR)/upgrade/openstack-part.tar centos ubuntu
	cd $(BUILD_DIR)/repos/nailgun/nailgun/nailgun/fixtures && tar rf $(BUILD_DIR)/upgrade/openstack-part.tar openstack.yaml

$(BUILD_DIR)/upgrade/fuel.done: \
		$(BUILD_DIR)/upgrade/fuel-part.done
	cd $(ISO_ROOT)/docker/images/ && tar cf $(BUILD_DIR)/upgrade/fuel-part.tar fuel-images.tar.lrz
	tar zcf $(BUILD_DIR)/upgrade/master-upgrade-$(PRODUCT_VERSION).tar.gz @$(BUILD_DIR)/upgrade/fuel-part.tar.gz @$(BUILD_DIR)/upgrade/common-part.tar

$(BUILD_DIR)/upgrade/openstack-part.done: \
		$(BUILD_DIR)/upgrade/openstack-part.done
	tar zcf $(BUILD_DIR)/upgrade/openstack-upgrade-$(PRODUCT_VERSION).tar.gz @$(BUILD_DIR)/upgrade/openstack-part.tar.gz @$(BUILD_DIR)/upgrade/common-part.tar
