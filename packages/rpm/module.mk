.PHONY: clean clean-rpm

clean: clean-rpm

clean-rpm:
	-sudo umount $(BUILD_DIR)/packages/rpm/SANDBOX/proc
	-sudo umount $(BUILD_DIR)/packages/rpm/SANDBOX/dev
	sudo rm -rf $(BUILD_DIR)/packages/rpm

RPM_SOURCES:=$(BUILD_DIR)/packages/rpm/SOURCES

# Usage:
# (eval (call prepare_source,package_name,file_name,source_path))
define prepare_source
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/rpm/sources/$1/$2
$(BUILD_DIR)/packages/rpm/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/rpm/sources/$1
ifeq ($1,nailgun-mcagents)
	cd $3 && tar zcf $(BUILD_DIR)/packages/rpm/sources/$1/$2 *
else
ifeq ($(findstring .tar.gz,$2),.tar.gz)
ifeq ($1,nailgun)
	cd $3 && npm install && grunt build
endif # /nailgun
	cd $3 && python setup.py sdist -d $(BUILD_DIR)/packages/rpm/sources/$1
else # not tar.gz
	cp $3 $(BUILD_DIR)/packages/rpm/sources/$1/$2
endif # /tar.gz
endif # /mcagents
endef

# Usage:
# (eval (call build_rpm,package_name))
define build_rpm
$(BUILD_DIR)/packages/rpm/repo.done: $(BUILD_DIR)/packages/rpm/$1.done
$(BUILD_DIR)/packages/rpm/repo.done: $(BUILD_DIR)/packages/rpm/$1-repocleanup.done

$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/mirror/src/build.done

$(BUILD_DIR)/packages/rpm/$1.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX
$(BUILD_DIR)/packages/rpm/$1.done: export SANDBOX_UP:=$$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/$1.done: export SANDBOX_DOWN:=$$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/$1.done: \
		$(SOURCE_DIR)/packages/rpm/specs/$1.spec \
		$(BUILD_DIR)/repos/repos.done
	mkdir -p $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	sudo sh -c "$$$${SANDBOX_UP}"
	sudo mkdir -p $$(SANDBOX)/tmp/SOURCES
	sudo cp -r $(BUILD_DIR)/packages/rpm/sources/$1/* $$(SANDBOX)/tmp/SOURCES
	sudo cp $(SOURCE_DIR)/packages/rpm/specs/$1.spec $$(SANDBOX)/tmp
	sudo chroot $$(SANDBOX) rpmbuild --nodeps -vv --define "_topdir /tmp" -ba /tmp/$1.spec
	cp $$(SANDBOX)/tmp/RPMS/*/$1-*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	sudo sh -c "$$$${SANDBOX_DOWN}"
	$$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/$1-repocleanup.done:
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages -regex '.*/$1-[^-]+-[^-]+' -delete
	$$(ACTION.TOUCH)
endef

$(eval $(call prepare_source,fencing-agent,fencing-agent.rb,$(BUILD_DIR)/repos/nailgun/bin/fencing-agent.rb))
$(eval $(call prepare_source,fencing-agent,fencing-agent.cron,$(BUILD_DIR)/repos/nailgun/bin/fencing-agent.cron))
$(eval $(call prepare_source,fuel-ostf,fuel-ostf-0.1.tar.gz,$(BUILD_DIR)/repos/ostf))
$(eval $(call prepare_source,fuelmenu,fuelmenu-0.1.tar.gz,$(BUILD_DIR)/repos/nailgun/fuelmenu))
$(eval $(call prepare_source,nailgun-agent,agent,$(BUILD_DIR)/repos/nailgun/bin/agent))
$(eval $(call prepare_source,nailgun-agent,nailgun-agent.cron,$(BUILD_DIR)/repos/nailgun/bin/nailgun-agent.cron))
$(eval $(call prepare_source,nailgun-mcagents,mcagents.tar.gz,$(BUILD_DIR)/repos/astute/mcagents))
$(eval $(call prepare_source,nailgun-net-check,nailgun-net-check-0.2.tar.gz,$(BUILD_DIR)/repos/nailgun/network_checker))
$(eval $(call prepare_source,nailgun,nailgun-0.1.0.tar.gz,$(BUILD_DIR)/repos/nailgun/nailgun))
$(eval $(call prepare_source,python-fuelclient,fuelclient-0.2.tar.gz,$(BUILD_DIR)/repos/nailgun/fuelclient))
$(eval $(call prepare_source,shotgun,Shotgun-0.1.0.tar.gz,$(BUILD_DIR)/repos/nailgun/shotgun))
$(eval $(call prepare_source,nailgun-redhat-license,get_redhat_licenses,$(SOURCE_DIR)/packages/rpm/nailgun-redhat-license/get_redhat_licenses))

$(eval $(call build_rpm,fencing-agent))
$(eval $(call build_rpm,fuelmenu))
$(eval $(call build_rpm,nailgun-mcagents))
$(eval $(call build_rpm,nailgun-net-check))
$(eval $(call build_rpm,nailgun))
$(eval $(call build_rpm,shotgun))
$(eval $(call build_rpm,fuel-ostf))
$(eval $(call build_rpm,nailgun-agent))
$(eval $(call build_rpm,nailgun-redhat-license))
$(eval $(call build_rpm,python-fuelclient))

$(BUILD_DIR)/packages/rpm/repo.done:
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
