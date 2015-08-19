.PHONY: all upgrade-lrzip openstack-yaml
.DELETE_ON_ERROR: $(UPGRADE_TARBALL_PATH).lrz
.DELETE_ON_ERROR: $(BUILD_DIR)/upgrade/common-part.tar
.DELETE_ON_ERROR: $(BUILD_DIR)/upgrade/openstack-part.tar
.DELETE_ON_ERROR: $(BUILD_DIR)/upgrade/$(SAVE_UPGRADE_PIP_ART)
.DELETE_ON_ERROR: $(BUILD_DIR)/upgrade/openstack-part.tar

all: upgrade-lrzip openstack-yaml

upgrade-lrzip: UPGRADERS ?= "host-system docker openstack"
upgrade-lrzip: $(UPGRADE_TARBALL_PATH).lrz

########################
# UPGRADE LRZIP ARTIFACT
########################
$(UPGRADE_TARBALL_PATH).lrz: \
		$(BUILD_DIR)/upgrade/openstack-part.done \
		$(BUILD_DIR)/upgrade/common-part.tar
	mkdir -p $(@D)
	rm -f $(BUILD_DIR)/upgrade/upgrade-lrzip.tar
	tar Af $(BUILD_DIR)/upgrade/upgrade-lrzip.tar $(BUILD_DIR)/upgrade/openstack-part.tar
	tar Af $(BUILD_DIR)/upgrade/upgrade-lrzip.tar $(BUILD_DIR)/upgrade/common-part.tar
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
ifeq ($(USE_UPGRADE_PIP_ART_HTTP_LINK),)
	echo "Using mirror pip-install approach"
	$(BUILD_DIR)/upgrade/venv/bin/pip install -r $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade/requirements.txt --download $(BUILD_DIR)/upgrade/deps --no-use-wheel
else
	echo "Using artifact from $(USE_UPGRADE_PIP_ART_HTTP_LINK) for pip-install"
	wget -v --no-check-certificate $(USE_UPGRADE_PIP_ART_HTTP_LINK) -O $(BUILD_DIR)/upgrade/deps.tar.gz.tmp
	mv $(BUILD_DIR)/upgrade/deps.tar.gz.tmp $(BUILD_DIR)/upgrade/deps.tar.gz
	mkdir -p $(BUILD_DIR)/upgrade/deps/
	tar xvf $(BUILD_DIR)/upgrade/deps.tar.gz --strip-components=1 -C $(BUILD_DIR)/upgrade/deps/
endif
	cd $(BUILD_DIR)/repos/nailgun/fuel_upgrade_system/fuel_upgrade && $(BUILD_DIR)/upgrade/venv/bin/python setup.py sdist --dist-dir $(BUILD_DIR)/upgrade/deps
	$(ACTION.TOUCH)

# Save pip artifact, if needed
$(BUILD_DIR)/upgrade/$(SAVE_UPGRADE_PIP_ART): $(BUILD_DIR)/upgrade/deps.done
	mkdir -p $(@D)
	rm -f $@
	tar czf $@ -C $(BUILD_DIR)/upgrade deps

$(ARTS_DIR)/$(SAVE_UPGRADE_PIP_ART): $(BUILD_DIR)/upgrade/$(SAVE_UPGRADE_PIP_ART)
	$(ACTION.COPY)

########################
# COMMON PART
########################
$(BUILD_DIR)/upgrade/common-part.tar: \
		$(ARTS_DIR)/$(VERSION_YAML_ART_NAME) \
		$(BUILD_DIR)/upgrade/deps.done
	mkdir -p $(@D)
	rm -f $@
	tar rf $@ -C $(BUILD_DIR)/upgrade --xform s:^:upgrade/: deps
	sed 's/{{UPGRADERS}}/${UPGRADERS}/g' $(SOURCE_DIR)/upgrade/upgrade_template.sh > $(BUILD_DIR)/upgrade/upgrade.sh
	tar rf $@ --mode=755 -C $(BUILD_DIR)/upgrade upgrade.sh
	tar rf $@ --mode=755 -C $(ARTS_DIR) --xform s:^:upgrade/config/: $(VERSION_YAML_ART_NAME)

ifneq ($(SAVE_UPGRADE_PIP_ART),)
$(BUILD_DIR)/upgrade/common-part.tar: $(ARTS_DIR)/$(SAVE_UPGRADE_PIP_ART)
endif


########################
# OPENSTACK PART
########################
$(BUILD_DIR)/upgrade/openstack_version: $(ARTS_DIR)/$(OPENSTACK_YAML_ART_NAME)
	python -c "import yaml; print filter(lambda r: r['fields'].get('name'), yaml.load(open('$(ARTS_DIR)/$(OPENSTACK_YAML_ART_NAME)')))[0]['fields']['version']" > $@

$(BUILD_DIR)/upgrade/openstack-part.done: CENTOS_REPO_ART=$(CENTOS_REPO_ART_NAME)
$(BUILD_DIR)/upgrade/openstack-part.done: CENTOS_REPO_ART_TOPDIR=centos-repo
$(BUILD_DIR)/upgrade/openstack-part.done: UBUNTU_REPO_ART=$(UBUNTU_REPO_ART_NAME)
$(BUILD_DIR)/upgrade/openstack-part.done: UBUNTU_REPO_ART_TOPDIR=ubuntu-repo
$(BUILD_DIR)/upgrade/openstack-part.done: $(ARTS_DIR)/$(CENTOS_REPO_ART_NAME)
$(BUILD_DIR)/upgrade/openstack-part.done: $(ARTS_DIR)/$(UBUNTU_REPO_ART_NAME)
$(BUILD_DIR)/upgrade/openstack-part.done: BASE=$(BUILD_DIR)/upgrade/openstack-part
$(BUILD_DIR)/upgrade/openstack-part.done: OPENSTACK_VERSION=$(shell cat $(BUILD_DIR)/upgrade/openstack_version)
$(BUILD_DIR)/upgrade/openstack-part.done: CENTOS_BASE=$(BASE)/upgrade/repos/$(OPENSTACK_VERSION)/centos/x86_64
$(BUILD_DIR)/upgrade/openstack-part.done: UBUNTU_BASE=$(BASE)/upgrade/repos/$(OPENSTACK_VERSION)/ubuntu/x86_64
$(BUILD_DIR)/upgrade/openstack-part.done: RELEASES_BASE=$(BASE)/upgrade/releases
$(BUILD_DIR)/upgrade/openstack-part.done: RELEASE_VERSIONS_BASE=$(BASE)/upgrade/release_versions
$(BUILD_DIR)/upgrade/openstack-part.done: \
		$(BUILD_DIR)/upgrade/openstack_version \
		$(ARTS_DIR)/$(OPENSTACK_YAML_ART_NAME) \
		$(ARTS_DIR)/$(VERSION_YAML_ART_NAME)
	rm -f $@
	mkdir -p $(@D)
#	CENTOS REPO
	mkdir -p $(CENTOS_BASE)
	tar xf $(ARTS_DIR)/$(CENTOS_REPO_ART) -C $(CENTOS_BASE) --xform s:^$(CENTOS_REPO_ART_TOPDIR)/::
#	UBUNTU REPO
	mkdir -p $(UBUNTU_BASE)
	tar xf $(ARTS_DIR)/$(UBUNTU_REPO_ART) -C $(UBUNTU_BASE) --xform s:^$(UBUNTU_REPO_ART_TOPDIR)/::
#	OPENSTACK-YAML
	mkdir -p $(RELEASES_BASE)
	cp $(ARTS_DIR)/$(OPENSTACK_YAML_ART_NAME) $(RELEASES_BASE)/$(OPENSTACK_VERSION).yaml
#	VERSION-YAML
	mkdir -p $(RELEASE_VERSIONS_BASE)
	cp $(ARTS_DIR)/$(VERSION_YAML_ART_NAME) $(RELEASE_VERSIONS_BASE)/$(OPENSTACK_VERSION).yaml
#   This is for backward compatibility with upgrade script.
#   It tries to figure out whether a particular update bundle diffirential or not.
	echo "diff_releases: {}" > $(RELEASES_BASE)/metadata.yaml
#	ARCHIVING
	tar rf $(BUILD_DIR)/upgrade/openstack-part.tar -C $(BASE) .
	$(ACTION.TOUCH)
