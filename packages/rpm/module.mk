.PHONY: clean clean-rpm

clean: clean-rpm

clean-rpm:
	-sudo umount $(shell readlink -f -m $(BUILD_DIR)/packages/rpm/SANDBOX/proc)
	-sudo umount $(shell readlink -f -m $(BUILD_DIR)/packages/rpm/SANDBOX/dev)
	sudo rm -rf $(BUILD_DIR)/packages/rpm

RPM_SOURCES:=$(BUILD_DIR)/packages/rpm/SOURCES

$(BUILD_DIR)/packages/rpm/prep.done: $(BUILD_DIR)/mirror/build.done
	mkdir -p $(RPM_SOURCES)
	cp -f $(LOCAL_MIRROR_SRC)/* $(RPM_SOURCES)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/rpm-cirros.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/cirros-0.3.0.spec
	rpmbuild -vv --define "_topdir `readlink -f $(BUILD_DIR)/packages/rpm`" -ba \
		$(SOURCE_DIR)/packages/rpm/specs/cirros-0.3.0.spec
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/rpm-nailgun-agent.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-agent.spec \
		$(call find-files,$(SOURCE_DIR)/bin)
	cp -f bin/agent bin/nailgun-agent.cron $(RPM_SOURCES)
	rpmbuild -vv --define "_topdir `readlink -f $(BUILD_DIR)/packages/rpm`" -ba \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-agent.spec
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/rpm-nailgun-mcagents.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-mcagents.spec \
		$(call find-files,$(SOURCE_DIR)/mcagent)
	mkdir -p $(BUILD_DIR)/packages/rpm/SOURCES/nailgun-mcagents
	cp -f $(SOURCE_DIR)/mcagent/* $(RPM_SOURCES)/nailgun-mcagents
	rpmbuild -vv --define "_topdir `readlink -f $(BUILD_DIR)/packages/rpm`" -ba \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-mcagents.spec
	$(ACTION.TOUCH)


$(BUILD_DIR)/packages/rpm/sandbox-packages.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX
$(BUILD_DIR)/packages/rpm/sandbox-packages.done: export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/sandbox-packages.done: export SANDBOX_DOWN:=$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/sandbox-packages.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-net-check.spec \
		$(SOURCE_DIR)/packages/rpm/nailgun-net-check/net_probe.py \
		$(SOURCE_DIR)/packages/rpm/specs/rbenv-ruby-1.9.3-p392.spec

	sudo sh -c "$${SANDBOX_UP}"

	cp -f $(SOURCE_DIR)/packages/rpm/patches/* $(RPM_SOURCES)
	sudo mkdir -p $(SANDBOX)/tmp/SOURCES
	sudo cp $(SOURCE_DIR)/packages/rpm/patches/* $(SANDBOX)/tmp/SOURCES
	sudo cp $(LOCAL_MIRROR_SRC)/* $(SANDBOX)/tmp/SOURCES

	sudo cp $(SOURCE_DIR)/packages/rpm/nailgun-net-check/net_probe.py $(SANDBOX)/tmp/SOURCES
	sudo cp $(SOURCE_DIR)/packages/rpm/specs/nailgun-net-check.spec $(SANDBOX)/tmp
	sudo chroot $(SANDBOX) rpmbuild -vv --define "_topdir /tmp" -ba /tmp/nailgun-net-check.spec

	sudo cp $(SOURCE_DIR)/packages/rpm/specs/rbenv-ruby-1.9.3-p392.spec $(SANDBOX)/tmp
	sudo chroot $(SANDBOX) rpmbuild -vv --define "_topdir /tmp" -ba /tmp/rbenv-ruby-1.9.3-p392.spec

	sudo unzip -q $(SANDBOX)/tmp/SOURCES/9f8d2ec75ba326d2a37884224698f3f96ff01629.zip -d $(SANDBOX)/tmp/SOURCES
	sudo rm -rf $(SANDBOX)/tmp/SOURCES/mcollective
	sudo mv $(SANDBOX)/tmp/SOURCES/marionette-collective-9f8d2ec75ba326d2a37884224698f3f96ff01629 $(SANDBOX)/tmp/SOURCES/mcollective
	sudo chroot $(SANDBOX) sh -c "mkdir -p ~/rpmbuild/SOURCES ~/rpmbuild/SPECS && cd /tmp/SOURCES/mcollective && rake rpm && rake gem"
	cp $(SANDBOX)/tmp/SOURCES/mcollective/build/*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64/
	cp $(SANDBOX)/tmp/SOURCES/mcollective/build/*.gem $(LOCAL_MIRROR_GEMS)/gems/

	cp $(SANDBOX)/tmp/RPMS/x86_64/* $(BUILD_DIR)/packages/rpm/RPMS/x86_64/
	sudo sh -c "$${SANDBOX_DOWN}"
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/repo.done: \
		$(BUILD_DIR)/packages/rpm/rpm-cirros.done \
		$(BUILD_DIR)/packages/rpm/rpm-nailgun-agent.done \
		$(BUILD_DIR)/packages/rpm/rpm-nailgun-mcagents.done \
		$(BUILD_DIR)/packages/rpm/sandbox-packages.done
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g `readlink -f "$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/repodata/comps.xml"` \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/build.done: $(BUILD_DIR)/packages/rpm/repo.done
	$(ACTION.TOUCH)