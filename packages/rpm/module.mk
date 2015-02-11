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

$(BUILD_DIR)/packages/rpm/buildd.tar.gz: SANDBOX_PACKAGES:=ruby rpm-build tar python-setuptools python-pbr
$(BUILD_DIR)/packages/rpm/buildd.tar.gz: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX/buildd
$(BUILD_DIR)/packages/rpm/buildd.tar.gz: export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/buildd.tar.gz: export SANDBOX_DOWN:=$(SANDBOX_DOWN)

$(BUILD_DIR)/packages/rpm/buildd.tar.gz: $(BUILD_DIR)/mirror/centos/repo.done
	sh -c "$${SANDBOX_UP}"
	sh -c "$${SANDBOX_DOWN}"
	sudo tar czf $@.tmp -C $(SANDBOX) .
	mv $@.tmp $@


# Usage:
# (eval (call build_rpm,package_name))
define build_rpm
$(BUILD_DIR)/packages/rpm/repo.done: $(BUILD_DIR)/packages/rpm/$1.done
$(BUILD_DIR)/packages/rpm/repo.done: $(BUILD_DIR)/packages/rpm/$1-repocleanup.done

# You can use package name as a target, for example: make ruby21-rubygem-astute
# It will build astute rpm package
$1: $(BUILD_DIR)/packages/rpm/$1.done

$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/mirror/centos/repo.done
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/source_$1.done
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/rpm/buildd.tar.gz


$(BUILD_DIR)/packages/rpm/$1.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX/$1
$(BUILD_DIR)/packages/rpm/$1.done: export SANDBOX_UP:=$$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/$1.done: export SANDBOX_DOWN:=$$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/$1.done: \
		$(SOURCE_DIR)/packages/rpm/specs/$1.spec \
		$(BUILD_DIR)/repos/repos.done
	mkdir -p $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	mkdir -p $$(SANDBOX) && \
	sudo tar xzf $(BUILD_DIR)/packages/rpm/buildd.tar.gz -C $$(SANDBOX) && \
	sudo mount --bind /proc $$(SANDBOX)/proc && \
	sudo mount --bind /dev $$(SANDBOX)/dev && \
	mkdir -p $$(SANDBOX)/tmp/SOURCES && \
	sudo cp -r $(BUILD_DIR)/packages/sources/$1/* $$(SANDBOX)/tmp/SOURCES && \
	sudo cp $(SOURCE_DIR)/packages/rpm/specs/$1.spec $$(SANDBOX)/tmp && \
	sudo chroot $$(SANDBOX) rpmbuild --nodeps -vv --define "_topdir /tmp" -ba /tmp/$1.spec
	cp $$(SANDBOX)/tmp/RPMS/*/$1-*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	sudo sh -c "$$$${SANDBOX_DOWN}"
	$$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: $(BUILD_DIR)/mirror/centos/repo.done
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages -regex '.*/$1-[^-]+-[^-]+' -delete
	$$(ACTION.TOUCH)
endef

fuel_rpm_packages:=\
fencing-agent \
fuel-agent \
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

$(eval $(foreach pkg,$(fuel_rpm_packages),$(call build_rpm,$(pkg))$(NEWLINE)))


$(BUILD_DIR)/packages/rpm/repo.done:
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/fuel-docker-images.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX/fuel-docker-images
$(BUILD_DIR)/packages/rpm/fuel-docker-images.done: export SANDBOX_DOWN:=$(SANDBOX_DOWN)

$(BUILD_DIR)/packages/rpm/fuel-docker-images.done: \
		$(BUILD_DIR)/repos/repos.done \
		$(BUILD_DIR)/packages/rpm/buildd.tar.gz \
                $(BUILD_DIR)/docker/build.done
	mkdir -p $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	mkdir -p $(SANDBOX) && \
	sudo tar xzf $(BUILD_DIR)/packages/rpm/buildd.tar.gz -C $(SANDBOX) && \
	sudo mknod $(SANDBOX)/dev/null c 1 3 && \
	sudo mknod $(SANDBOX)/dev/random c 1 8 && \
	sudo chmod 666 $(SANDBOX)/dev/{null,random} && \
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

