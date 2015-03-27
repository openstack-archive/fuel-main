.PHONY: all upgrade-lrzip openstack-yaml upgrade_versions
.DELETE_ON_ERROR: $(UPGRADE_TARBALL_PATH).lrz
.DELETE_ON_ERROR: $(BUILD_DIR)/upgrade/common-part.tar
.DELETE_ON_ERROR: $(BUILD_DIR)/upgrade/fuel-lrzip-part.tar.tar
.DELETE_ON_ERROR: $(BUILD_DIR)/upgrade/openstack-part.tar

all: upgrade-lrzip openstack-yaml

upgrade-lrzip: UPGRADERS ?= "host-system bootstrap docker openstack targetimages"
upgrade-lrzip: $(UPGRADE_TARBALL_PATH).lrz

########################
# UPGRADE LRZIP ARTIFACT
########################
$(UPGRADE_TARBALL_PATH).lrz: \
		$(BUILD_DIR)/upgrade/openstack-part.done \
		$(BUILD_DIR)/upgrade/fuel-lrzip-part.tar \
		$(BUILD_DIR)/upgrade/common-part.tar \
		$(BUILD_DIR)/upgrade/image-part.tar
	mkdir -p $(@D)
	rm -f $(BUILD_DIR)/upgrade/upgrade-lrzip.tar
	tar Af $(BUILD_DIR)/upgrade/upgrade-lrzip.tar $(BUILD_DIR)/upgrade/fuel-lrzip-part.tar
	tar Af $(BUILD_DIR)/upgrade/upgrade-lrzip.tar $(BUILD_DIR)/upgrade/openstack-part.tar
	tar Af $(BUILD_DIR)/upgrade/upgrade-lrzip.tar $(BUILD_DIR)/upgrade/common-part.tar
	tar Af $(BUILD_DIR)/upgrade/upgrade-lrzip.tar $(BUILD_DIR)/upgrade/image-part.tar
	lrzip -L2 -U -D -f $(BUILD_DIR)/upgrade/upgrade-lrzip.tar -o $@

########################
# OPENSTACK_YAML ARTIFACT
########################
openstack-yaml: $(ARTS_DIR)/$(OPENSTACK_YAML_ART_NAME)

$(ARTS_DIR)/$(OPENSTACK_YAML_ART_NAME): $(BUILD_DIR)/upgrade/$(OPENSTACK_YAML_ART_NAME)
	$(ACTION.COPY)

$(BUILD_DIR)/upgrade/$(OPENSTACK_YAML_ART_NAME): $(BUILD_DIR)/repos/nailgun.done
	mkdir -p $(@D)
	cp $(BUILD_DIR)/repos/nailgun/nailgun/nailgun/fixtures/openstack.yaml $@

########################
# UPGRADE DEPENDENCIES
########################
$(BUILD_DIR)/upgrade/deps.done: \
		$(BUILD_DIR)/repos/nailgun.done
	mkdir -p $(BUILD_DIR)/upgrade/deps
	virtualenv $(BUILD_DIR)/upgrade/venv
#	Requires virtualenv, pip, python-dev packages
	$(BUILD_DIR)/upgrade/venv/bin/pip install -r $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade/requirements.txt --download $(BUILD_DIR)/upgrade/deps --no-use-wheel
	cd $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade && $(BUILD_DIR)/upgrade/venv/bin/python setup.py sdist --dist-dir $(BUILD_DIR)/upgrade/deps
	$(ACTION.TOUCH)

########################
# COMMON PART
########################
$(BUILD_DIR)/upgrade/common-part.tar: \
		$(BUILD_DIR)/repos/fuellib.done \
		$(BUILD_DIR)/upgrade/deps.done
	mkdir -p $(@D)
	rm -f $@
	tar cf $@ -C $(BUILD_DIR)/repos/fuellib/deployment --xform s:^puppet:upgrade/puppet/modules: puppet
	tar rf $@ -C $(BUILD_DIR)/repos/fuellib/deployment/puppet/osnailyfacter/examples --xform s:^:upgrade/puppet/manifests/: site.pp
	tar rf $@ -C $(BUILD_DIR)/upgrade --xform s:^:upgrade/: deps
	sed 's/{{UPGRADERS}}/${UPGRADERS}/g' $(SOURCE_DIR)/upgrade/upgrade_template.sh > $(BUILD_DIR)/upgrade/upgrade.sh
	tar rf $@ --mode=755 -C $(BUILD_DIR)/upgrade upgrade.sh

########################
# FUEL LRZIP PART
########################
$(BUILD_DIR)/upgrade/fuel-lrzip-part.tar: \
		$(BUILD_DIR)/bootstrap/build.done \
		$(ISOROOT)/version.yaml \
		$(BUILD_DIR)/docker/build.done
	mkdir -p $(@D)
	rm -f $@
	mkdir -p $(BUILD_DIR)/upgrade/images
	cd $(BUILD_DIR)/upgrade/images && lrzip -d $(BUILD_DIR)/docker/fuel-images.tar.lrz
	tar cf $@ -C $(BUILD_DIR) upgrade/images
	tar rf $@ -C $(BUILD_DIR)/iso/isoroot --xform s:^:upgrade/config/: version.yaml
	tar rf $@ -C $(BUILD_DIR)/bootstrap --xform s:^:upgrade/bootstrap/: initramfs.img linux

########################
# IMAGE PART
########################
$(BUILD_DIR)/upgrade/image-part.tar: \
		$(BUILD_DIR)/image/build.done
	mkdir -p $(BUILD_DIR)/upgrade/targetimages
	tar xf $(ARTS_DIR)/$(TARGET_CENTOS_IMG_ART_NAME) -C $(BUILD_DIR)/upgrade/targetimages
	rm -f $@
	tar cf $@ -C $(BUILD_DIR)/upgrade/targetimages . --xform s:^:upgrade/targetimages/:

########################
# OPENSTACK PART
########################
define build_openstack_part
# 1 - new vervion
# 2 - old version

ifeq ($(CURRENT_VERSION),$1)
ARTS_DIR_$1:=$(ARTS_DIR)
else
ARTS_DIR_$1:=$(DEPS_DIR)/$1
endif

$(BUILD_DIR)/upgrade/openstack_version_$1: $$(ARTS_DIR_$1)/$(OPENSTACK_YAML_ART_NAME)
	python -c "import yaml; print filter(lambda r: r['fields'].get('name'), yaml.load(open('$$(ARTS_DIR_$1)/$(OPENSTACK_YAML_ART_NAME)')))[0]['fields']['version']" > $$@

ifneq ($2,)
$(BUILD_DIR)/upgrade/openstack_version_$2: $(DEPS_DIR)/$2/$(OPENSTACK_YAML_ART_NAME)
	python -c "import yaml; print filter(lambda r: r['fields'].get('name'), yaml.load(open('$(DEPS_DIR)/$2/$(OPENSTACK_YAML_ART_NAME)')))[0]['fields']['version']" > $$@
endif

$(BUILD_DIR)/upgrade/openstack-part.done: $(BUILD_DIR)/upgrade/openstack-$1-part.done

.DELETE_ON_ERROR: $(BUILD_DIR)/upgrade/openstack-part.tar

ifneq ($2,)
$(BUILD_DIR)/upgrade/openstack-$1-part.done: CENTOS_REPO_ART=$(DIFF_CENTOS_REPO_ART_BASE)-$1-$2.tar
$(BUILD_DIR)/upgrade/openstack-$1-part.done: CENTOS_REPO_ART_TOPDIR=centos_updates-$1-$2
$(BUILD_DIR)/upgrade/openstack-$1-part.done: UBUNTU_REPO_ART=$(DIFF_UBUNTU_REPO_ART_BASE)-$1-$2.tar
$(BUILD_DIR)/upgrade/openstack-$1-part.done: UBUNTU_REPO_ART_TOPDIR=ubuntu_updates-$1-$2
$(BUILD_DIR)/upgrade/openstack-$1-part.done: $(BUILD_DIR)/upgrade/openstack_version_$2
$(BUILD_DIR)/upgrade/openstack-$1-part.done: $$(ARTS_DIR_$1)/$(DIFF_CENTOS_REPO_ART_BASE)-$1-$2.tar
$(BUILD_DIR)/upgrade/openstack-$1-part.done: $$(ARTS_DIR_$1)/$(DIFF_UBUNTU_REPO_ART_BASE)-$1-$2.tar
else
$(BUILD_DIR)/upgrade/openstack-$1-part.done: CENTOS_REPO_ART=$(CENTOS_REPO_ART_NAME)
$(BUILD_DIR)/upgrade/openstack-$1-part.done: CENTOS_REPO_ART_TOPDIR=centos-repo
$(BUILD_DIR)/upgrade/openstack-$1-part.done: UBUNTU_REPO_ART=$(UBUNTU_REPO_ART_NAME)
$(BUILD_DIR)/upgrade/openstack-$1-part.done: UBUNTU_REPO_ART_TOPDIR=ubuntu-repo
$(BUILD_DIR)/upgrade/openstack-$1-part.done: $$(ARTS_DIR_$1)/$(CENTOS_REPO_ART_NAME)
$(BUILD_DIR)/upgrade/openstack-$1-part.done: $$(ARTS_DIR_$1)/$(UBUNTU_REPO_ART_NAME)
endif
$(BUILD_DIR)/upgrade/openstack-$1-part.done: BASE=$(BUILD_DIR)/upgrade/openstack-$1-part
$(BUILD_DIR)/upgrade/openstack-$1-part.done: OPENSTACK_VERSION=$$(shell cat $(BUILD_DIR)/upgrade/openstack_version_$1)
$(BUILD_DIR)/upgrade/openstack-$1-part.done: CENTOS_BASE=$$(BASE)/upgrade/repos/$$(OPENSTACK_VERSION)/centos/x86_64
$(BUILD_DIR)/upgrade/openstack-$1-part.done: UBUNTU_BASE=$$(BASE)/upgrade/repos/$$(OPENSTACK_VERSION)/ubuntu/x86_64
$(BUILD_DIR)/upgrade/openstack-$1-part.done: PUPPET_BASE=$$(BASE)/upgrade/puppet/$$(OPENSTACK_VERSION)
$(BUILD_DIR)/upgrade/openstack-$1-part.done: RELEASES_BASE=$$(BASE)/upgrade/releases
$(BUILD_DIR)/upgrade/openstack-$1-part.done: RELEASE_VERSIONS_BASE=$$(BASE)/upgrade/release_versions
$(BUILD_DIR)/upgrade/openstack-$1-part.done: \
		$(BUILD_DIR)/upgrade/openstack_version_$1 \
		$$(ARTS_DIR_$1)/$(OPENSTACK_YAML_ART_NAME) \
		$$(ARTS_DIR_$1)/$(VERSION_YAML_ART_NAME) \
		$$(ARTS_DIR_$1)/$(PUPPET_ART_NAME)
	rm -f $$@
	mkdir -p $$(@D)
#	CENTOS REPO
	mkdir -p $$(CENTOS_BASE)
	tar xf $$(ARTS_DIR_$1)/$$(CENTOS_REPO_ART) -C $$(CENTOS_BASE) --xform s:^$$(CENTOS_REPO_ART_TOPDIR)/::
#	UBUNTU REPO
	mkdir -p $$(UBUNTU_BASE)
	tar xf $$(ARTS_DIR_$1)/$$(UBUNTU_REPO_ART) -C $$(UBUNTU_BASE) --xform s:^$$(UBUNTU_REPO_ART_TOPDIR)/::
#	PUPPET MODULES
	mkdir -p $$(PUPPET_BASE)/modules
	tar zxf $$(ARTS_DIR_$1)/$(PUPPET_ART_NAME) -C $$(PUPPET_BASE)/modules --xform s:^puppet/::
#	PUPPET MANIFESTS
	mkdir -p $$(PUPPET_BASE)/manifests
	cp $$(PUPPET_BASE)/modules/osnailyfacter/examples/site.pp $$(PUPPET_BASE)/manifests
	cp $$(CENTOS_BASE)/centos-versions.yaml $$(PUPPET_BASE)/manifests
	cp $$(UBUNTU_BASE)/ubuntu-versions.yaml $$(PUPPET_BASE)/manifests
#	OPENSTACK-YAML
	mkdir -p $$(RELEASES_BASE)
	cp $$(ARTS_DIR_$1)/$(OPENSTACK_YAML_ART_NAME) $$(RELEASES_BASE)/$$(OPENSTACK_VERSION).yaml
#	METADATA-YAML
ifneq ($2,)
	grep -q "diff_releases:" $(BUILD_DIR)/upgrade/metadata.yaml 2>/dev/null || echo "diff_releases:" > $(BUILD_DIR)/upgrade/metadata.yaml
	echo "  $$(OPENSTACK_VERSION): $$(shell cat $(BUILD_DIR)/upgrade/openstack_version_$2)" >> $(BUILD_DIR)/upgrade/metadata.yaml
endif
#	VERSION-YAML
	mkdir -p $$(RELEASE_VERSIONS_BASE)
	cp $$(ARTS_DIR_$1)/$(VERSION_YAML_ART_NAME) $$(RELEASE_VERSIONS_BASE)/$$(OPENSTACK_VERSION).yaml
#	ARCHIVING
	tar rf $(BUILD_DIR)/upgrade/openstack-part.tar -C $$(BASE) .
	@mkdir -p $$(@D)
	touch $$@
endef


$(foreach diff,$(UPGRADE_VERSIONS),$(eval $(call build_openstack_part,$(shell echo $(diff) | awk -F':' '{print $$1}'),$(shell echo $(diff) | awk -F':' '{print $$2}'))))


$(BUILD_DIR)/upgrade/openstack-part.done:
	grep -q "diff_releases:" $(BUILD_DIR)/upgrade/metadata.yaml 2>/dev/null || echo "diff_releases: {}" > $(BUILD_DIR)/upgrade/metadata.yaml
	tar rf $(BUILD_DIR)/upgrade/openstack-part.tar -C $(BUILD_DIR)/upgrade/ metadata.yaml --xform s:^:upgrade/releases/:
	$(ACTION.TOUCH)
