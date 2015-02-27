.PHONY: clean clean-rpm

clean: clean-rpm

clean-rpm:
	-mount | grep '$(BUILD_DIR)/packages/rpm/SANDBOX' | while read entry; do \
		set -- $$entry; \
		mntpt="$$3"; \
		sudo umount $$mntpt; \
	done
	sudo rm -rf $(BUILD_DIR)/packages/rpm

RPM_SOURCES:=$(BUILD_DIR)/packages/rpm/SOURCES

fuel_rpm_packages:=\
fencing-agent \
fuel-agent \
fuel-image \
fuelmenu \
nailgun-mcagents \
ruby21-nailgun-mcagents \
nailgun-net-check \
python-tasklib \
nailgun \
shotgun \
fuel-ostf \
nailgun-agent \
nailgun-redhat-license \
python-fuelclient \
ruby21-rubygem-astute

ifeq ($(USE_MOCK),1)
include $(SOURCE_DIR)/packages/rpm/module_mock.mk
$(eval $(foreach pkg,$(fuel_rpm_packages),$(call build_rpm_in_mock,$(pkg))$(NEWLINE)))
else
include $(SOURCE_DIR)/packages/rpm/module_sandbox.mk
$(eval $(foreach pkg,$(fuel_rpm_packages),$(call build_rpm,$(pkg))$(NEWLINE)))
endif

$(BUILD_DIR)/packages/rpm/fuel-docker-images.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX/fuel-docker-images
$(BUILD_DIR)/packages/rpm/fuel-docker-images.done: export SANDBOX_DOWN:=$(SANDBOX_DOWN)

$(BUILD_DIR)/packages/rpm/fuel-docker-images.done: \
		$(BUILD_DIR)/repos/repos.done \
		$(BUILD_DIR)/packages/rpm/buildd.tar.gz \
		$(BUILD_DIR)/docker/build.done
	mkdir -p $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	mkdir -p $(SANDBOX) && \
	sudo tar xzf $(BUILD_DIR)/packages/rpm/buildd.tar.gz -C $(SANDBOX) && \
	mkdir -p $(SANDBOX)/tmp/SOURCES && \
	sudo cp -r $(BUILD_DIR)/docker/$(DOCKER_ART_NAME) $(SANDBOX)/tmp/SOURCES && \
	(cd $(BUILD_DIR)/docker && sudo tar czf $(SANDBOX)/tmp/SOURCES/fuel-images-sources.tar.gz sources utils) && \
	sudo cp $(SOURCE_DIR)/packages/rpm/specs/fuel-docker-images.spec $(SANDBOX)/tmp && \
	sudo chroot $(SANDBOX) rpmbuild --nodeps -vv --define "_topdir /tmp" -ba /tmp/fuel-docker-images.spec
	cp $(SANDBOX)/tmp/RPMS/*/fuel-docker-images-*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' | xargs cp -u --target-directory=$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/build.done: $(BUILD_DIR)/packages/rpm/repo.done
	$(ACTION.TOUCH)
