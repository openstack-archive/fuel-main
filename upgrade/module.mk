.PHONY: upgrade fuel-upgrade openstack-upgrade

upgrade: UPGRADERS ?= "docker host-system openstack"
upgrade: $(BUILD_DIR)/upgrade/upgrade.done

fuel-upgrade: UPGRADERS ?= "docker host-system"
fuel-upgrade: $(BUILD_DIR)/upgrade/fuel.done

openstack-upgrade: UPGRADERS ?= "openstack"
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
	tar cf $(BUILD_DIR)/upgrade/common-part.tar -C $(BUILD_DIR)/repos/fuellib/deployment --xform s:^puppet:upgrade/puppet/modules: puppet
	tar rf $(BUILD_DIR)/upgrade/common-part.tar -C $(BUILD_DIR)/repos/fuellib/deployment/puppet/osnailyfacter/examples --xform s:^:upgrade/puppet/manifests/: site.pp
	# Requires virtualenv, pip, python-dev packages
	virtualenv $(BUILD_DIR)/upgrade/venv
	$(BUILD_DIR)/upgrade/venv/bin/pip install -r $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade/requirements.txt
	$(BUILD_DIR)/upgrade/venv/bin/pip install $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade
	tar rf $(BUILD_DIR)/upgrade/common-part.tar -C $(BUILD_DIR)/upgrade/venv/lib/python* --xform s:^:upgrade/: site-packages
	tar rf $(BUILD_DIR)/upgrade/common-part.tar -C $(BUILD_DIR)/upgrade/venv --xform s:^:upgrade/: bin/fuel-upgrade
	sed 's/{{UPGRADERS}}/${UPGRADERS}/g' $(SOURCE_DIR)/upgrade/upgrade_template.sh > $(BUILD_DIR)/upgrade/upgrade.sh
	tar rf $(BUILD_DIR)/upgrade/common-part.tar --mode=755 -C $(BUILD_DIR)/upgrade upgrade.sh
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
	tar cf $(BUILD_DIR)/upgrade/openstack-part.tar -C $(LOCAL_MIRROR) --xform s:^centos/os/x86_64:upgrade/repos/centos/x86_64: centos/os/x86_64
	tar rf $(BUILD_DIR)/upgrade/openstack-part.tar -C $(LOCAL_MIRROR) --xform s:^ubuntu:upgrade/repos/ubuntu/x86_64: ubuntu
	tar rf $(BUILD_DIR)/upgrade/openstack-part.tar -C $(BUILD_DIR)/repos/nailgun/nailgun/nailgun/fixtures --xform s:^:upgrade/config/: openstack.yaml
	tar rf $(BUILD_DIR)/upgrade/openstack-part.tar -C $(ISOROOT) --xform s:^:upgrade/puppet/manifests/: centos-versions.yaml ubuntu-versions.yaml
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
