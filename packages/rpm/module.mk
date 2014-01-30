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
		$(BUILD_DIR)/repos/nailgun.done \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/bin)
	cp -f $(BUILD_DIR)/repos/nailgun/bin/agent $(BUILD_DIR)/repos/nailgun/bin/nailgun-agent.cron $(RPM_SOURCES)
	rpmbuild -vv --define "_topdir $(BUILD_DIR)/packages/rpm" -ba \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-agent.spec
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/rpm-nailgun-mcagents.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-mcagents.spec \
		$(BUILD_DIR)/repos/astute.done \
		$(call find-files,$(BUILD_DIR)/astute/mcagents)
	mkdir -p $(BUILD_DIR)/packages/rpm/SOURCES/nailgun-mcagents
	cp -f $(BUILD_DIR)/repos/astute/mcagents/* $(RPM_SOURCES)/nailgun-mcagents
	rpmbuild -vv --define "_topdir $(BUILD_DIR)/packages/rpm" -ba \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-mcagents.spec
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/rpm-dhcp-checker.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX
$(BUILD_DIR)/packages/rpm/rpm-dhcp-checker.done: export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/rpm-dhcp-checker.done: export SANDBOX_DOWN:=$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/rpm-dhcp-checker.done: $(BUILD_DIR)/repos/nailgun.done
$(BUILD_DIR)/packages/rpm/rpm-dhcp-checker.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/dhcp-checker.spec \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/dhcp-checker)
	sudo sh -c "$${SANDBOX_UP}"
	sudo mkdir -p $(SANDBOX)/tmp/SOURCES
	sudo cp $(LOCAL_MIRROR_SRC)/* $(SANDBOX)/tmp/SOURCES
	sudo cp -r $(BUILD_DIR)/repos/nailgun/dhcp-checker/* $(SANDBOX)/tmp/SOURCES/
	sudo cp $(SOURCE_DIR)/packages/rpm/specs/dhcp-checker.spec $(SANDBOX)/tmp
	sudo chroot $(SANDBOX) rpmbuild -vv --define "_topdir /tmp" -ba /tmp/dhcp-checker.spec
	cp $(SANDBOX)/tmp/RPMS/noarch/dhcp_checker-*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64/
	sudo sh -c "$${SANDBOX_DOWN}"
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/rpm-python-fuelclient.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX
$(BUILD_DIR)/packages/rpm/rpm-python-fuelclient.done: export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/rpm-python-fuelclient.done: export SANDBOX_DOWN:=$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/rpm-python-fuelclient.done: $(BUILD_DIR)/repos/nailgun.done
$(BUILD_DIR)/packages/rpm/rpm-python-fuelclient.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/python-fuelclient.spec \
		$(call find-files,$(BUILD_DIR)/repos/nailgun/fuelclient)
	sudo sh -c "$${SANDBOX_UP}"
	sudo mkdir -p $(SANDBOX)/tmp/SOURCES/python-fuelclient
	sudo cp -r $(BUILD_DIR)/repos/nailgun/fuelclient/* $(SANDBOX)/tmp/SOURCES/python-fuelclient
	cd $(SANDBOX)/tmp/SOURCES/python-fuelclient && sudo python setup.py sdist -d $(SANDBOX)/tmp/SOURCES
	sudo cp $(SOURCE_DIR)/packages/rpm/specs/python-fuelclient.spec $(SANDBOX)/tmp
	sudo chroot $(SANDBOX) rpmbuild -vv --define "_topdir /tmp" -ba /tmp/python-fuelclient.spec
	cp $(SANDBOX)/tmp/RPMS/noarch/python-fuelclient-*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64/
	sudo sh -c "$${SANDBOX_DOWN}"
	$(ACTION.TOUCH)


$(BUILD_DIR)/packages/rpm/rpm-fuelmenu.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX
$(BUILD_DIR)/packages/rpm/rpm-fuelmenu.done: export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/rpm-fuelmenu.done: export SANDBOX_DOWN:=$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/rpm-fuelmenu.done: \
               $(BUILD_DIR)/packages/rpm/prep.done \
               $(SOURCE_DIR)/packages/rpm/specs/fuelmenu.spec \
               $(call find-files,$(BUILD_DIR)/repos/nailgun/fuelmenu)
	sudo sh -c "$${SANDBOX_UP}"
	sudo mkdir -p $(SANDBOX)/tmp/SOURCES/fuelmenu
	sudo cp -r $(BUILD_DIR)/repos/nailgun/fuelmenu/* $(SANDBOX)/tmp/SOURCES/fuelmenu
	cd $(SANDBOX)/tmp/SOURCES/fuelmenu && sudo python setup.py sdist -d $(SANDBOX)/tmp/SOURCES
	sudo cp $(SOURCE_DIR)/packages/rpm/specs/fuelmenu.spec $(SANDBOX)/tmp
	sudo chroot $(SANDBOX) rpmbuild -vv --define "_topdir /tmp" -ba /tmp/fuelmenu.spec
	cp $(SANDBOX)/tmp/RPMS/noarch/fuelmenu-*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64/
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

$(BUILD_DIR)/packages/rpm/rpm-nailgun-redhat-license.done: \
		$(BUILD_DIR)/packages/rpm/prep.done \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-redhat-license.spec \
		$(SOURCE_DIR)/packages/rpm/nailgun-redhat-license/get_redhat_licenses
	mkdir -p $(RPM_SOURCES)/nailgun-redhat-license
	cp -f $(SOURCE_DIR)/packages/rpm/nailgun-redhat-license/* $(RPM_SOURCES)/nailgun-redhat-license
	rpmbuild -vv --define "_topdir $(BUILD_DIR)/packages/rpm" -ba \
		$(SOURCE_DIR)/packages/rpm/specs/nailgun-redhat-license.spec
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/repo.done: \
		$(BUILD_DIR)/packages/rpm/rpm-nailgun-agent.done \
		$(BUILD_DIR)/packages/rpm/rpm-nailgun-mcagents.done \
		$(BUILD_DIR)/packages/rpm/rpm-nailgun-redhat-license.done \
		$(BUILD_DIR)/packages/rpm/rpm-rbenv-ruby.done \
		$(BUILD_DIR)/packages/rpm/rpm-dhcp-checker.done \
		$(BUILD_DIR)/packages/rpm/rpm-fuelmenu.done \
		$(BUILD_DIR)/packages/rpm/rpm-python-fuelclient.done
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
ifeq ($(CACHE_RHEL),1)
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_RHEL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_RHEL)/comps.xml \
		-o $(LOCAL_MIRROR_RHEL) $(LOCAL_MIRROR_RHEL)
endif
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/build.done: $(BUILD_DIR)/packages/rpm/repo.done
	$(ACTION.TOUCH)
