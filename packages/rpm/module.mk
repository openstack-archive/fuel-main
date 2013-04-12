.PHONY: clean clean-rpm

clean: clean-rpm

clean-rpm:
	-sudo umount $(BUILD_DIR)/packages/rpm/SANDBOX/proc
	-sudo umount $(BUILD_DIR)/packages/rpm/SANDBOX/dev
	sudo rm -rf $(BUILD_DIR)/packages/rpm

RPM_SOURCES:=$(BUILD_DIR)/packages/rpm/SOURCES

$(BUILD_DIR)/packages/rpm/prep.done: $(BUILD_DIR)/mirror/src/build.done
	mkdir -p $(RPM_SOURCES)
	cp -f $(LOCAL_MIRROR_SRC)/* $(RPM_SOURCES)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/rpm-nailgun-agent.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-agent.spec \
		$(call find-files,$(SOURCE_DIR)/bin)
	cp -f $(SOURCE_DIR)/bin/agent $(SOURCE_DIR)/bin/nailgun-agent.cron $(RPM_SOURCES)
	rpmbuild -vv --define "_topdir $(BUILD_DIR)/packages/rpm" -ba \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-agent.spec
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/rpm-nailgun-mcagents.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-mcagents.spec \
		$(call find-files,$(SOURCE_DIR)/astute/mcagents)
	mkdir -p $(BUILD_DIR)/packages/rpm/SOURCES/nailgun-mcagents
	cp -f $(SOURCE_DIR)/astute/mcagents/* $(RPM_SOURCES)/nailgun-mcagents
	rpmbuild -vv --define "_topdir $(BUILD_DIR)/packages/rpm" -ba \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-mcagents.spec
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/rpm-nailgun-net-check.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX
$(BUILD_DIR)/packages/rpm/rpm-nailgun-net-check.done: export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/rpm-nailgun-net-check.done: export SANDBOX_DOWN:=$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/rpm-nailgun-net-check.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-net-check.spec \
		$(SOURCE_DIR)/packages/rpm/nailgun-net-check/net_probe.py
	sudo sh -c "$${SANDBOX_UP}"
	sudo mkdir -p $(SANDBOX)/tmp/SOURCES
	sudo cp $(SOURCE_DIR)/packages/rpm/patches/* $(SANDBOX)/tmp/SOURCES
	sudo cp $(LOCAL_MIRROR_SRC)/* $(SANDBOX)/tmp/SOURCES
	sudo cp $(SOURCE_DIR)/packages/rpm/nailgun-net-check/net_probe.py $(SANDBOX)/tmp/SOURCES
	sudo cp $(SOURCE_DIR)/packages/rpm/specs/nailgun-net-check.spec $(SANDBOX)/tmp
	sudo chroot $(SANDBOX) rpmbuild -vv --define "_topdir /tmp" -ba /tmp/nailgun-net-check.spec
	cp $(SANDBOX)/tmp/RPMS/x86_64/nailgun-net-check-*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64/
	sudo sh -c "$${SANDBOX_DOWN}"
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/rpm-rbenv-ruby.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX
$(BUILD_DIR)/packages/rpm/rpm-rbenv-ruby.done: export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/rpm-rbenv-ruby.done: export SANDBOX_DOWN:=$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/rpm-rbenv-ruby.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/rbenv-ruby-1.9.3-p392.spec
	sudo sh -c "$${SANDBOX_UP}"
	sudo mkdir -p $(SANDBOX)/tmp/SOURCES
	sudo cp $(LOCAL_MIRROR_SRC)/* $(SANDBOX)/tmp/SOURCES
	sudo cp $(SOURCE_DIR)/packages/rpm/specs/rbenv-ruby-1.9.3-p392.spec $(SANDBOX)/tmp
	sudo chroot $(SANDBOX) rpmbuild -vv --define "_topdir /tmp" -ba /tmp/rbenv-ruby-1.9.3-p392.spec
	cp $(SANDBOX)/tmp/RPMS/x86_64/rbenv-ruby-*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64/
	sudo sh -c "$${SANDBOX_DOWN}"
	$(ACTION.TOUCH)

MCOLLECTIVE_COMMIT:=9f8d2ec75ba326d2a37884224698f3f96ff01629
$(BUILD_DIR)/packages/rpm/rpm-mcollective.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX
$(BUILD_DIR)/packages/rpm/rpm-mcollective.done: export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/rpm-mcollective.done: export SANDBOX_DOWN:=$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/rpm-mcollective.done: \
		$(BUILD_DIR)/packages/rpm/prep.done
	sudo sh -c "$${SANDBOX_UP}"
	sudo rm -rf $(SANDBOX)/tmp/marionette-collective-$(MCOLLECTIVE_COMMIT)
	unzip -q $(LOCAL_MIRROR_SRC)/$(MCOLLECTIVE_COMMIT).zip -d $(SANDBOX)/tmp
	sudo chroot $(SANDBOX) sh -c "mkdir -p ~/rpmbuild/SOURCES ~/rpmbuild/SPECS"
	sudo chroot $(SANDBOX) sh -c "cd /tmp/marionette-collective-$(MCOLLECTIVE_COMMIT) && rake rpm && rake gem"
	cp $(SANDBOX)/tmp/marionette-collective-$(MCOLLECTIVE_COMMIT)/build/*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64/
	cp $(SANDBOX)/tmp/marionette-collective-$(MCOLLECTIVE_COMMIT)/build/*.gem $(LOCAL_MIRROR_GEMS)/gems/
	(cd $(LOCAL_MIRROR_GEMS) && gem generate_index gems)
	sudo sh -c "$${SANDBOX_DOWN}"
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/repo.done: \
		$(BUILD_DIR)/packages/rpm/rpm-nailgun-agent.done \
		$(BUILD_DIR)/packages/rpm/rpm-nailgun-mcagents.done \
		$(BUILD_DIR)/packages/rpm/rpm-nailgun-net-check.done \
		$(BUILD_DIR)/packages/rpm/rpm-rbenv-ruby.done \
		$(BUILD_DIR)/packages/rpm/rpm-mcollective.done
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/repodata/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/build.done: $(BUILD_DIR)/packages/rpm/repo.done
	$(ACTION.TOUCH)
