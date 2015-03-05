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
$(BUILD_DIR)/packages/rpm/repo$2.done: $(BUILD_DIR)/packages/rpm/$1.done
$(BUILD_DIR)/packages/rpm/repo$2.done: $(BUILD_DIR)/packages/rpm/$1-repocleanup.done

# You can use package name as a target, for example: make ruby21-rubygem-astute
# It will build astute rpm package
$1: $(BUILD_DIR)/packages/rpm/$1.done

$(BUILD_DIR)/packages/rpm/$1.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX/$1
$(BUILD_DIR)/packages/rpm/$1.done: export SANDBOX_DOWN:=$$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/source_$1.done
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/rpm/buildd.tar.gz
$(BUILD_DIR)/packages/rpm/$1.done: $(SOURCE_DIR)/packages/rpm/specs/$1.spec
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

define UPDATE_REPO
find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \;
createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
	-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
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

$(BUILD_DIR)/packages/rpm/repo.done: export UPDATE_REPO:=$(UPDATE_REPO)
	sh -c "$${UPDATE_REPO}"
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/build.done: $(BUILD_DIR)/packages/rpm/repo.done
	$(ACTION.TOUCH)


#######################################
# This section is for building container
# packages that depend on other packages.
# For example, bootstrap image package
# assumes passing through the following build stages
# 1) upstream mirror
# 2) fuel packages
# 3) bootstrap image (depends on 1 and 2)
# 4) bootstrap image package (depends on 3)
#######################################

fuel_rpm_packages_late:=\
fuel-bootstrap-image

$(eval $(foreach pkg,$(fuel_rpm_packages),$(call build_rpm,$(pkg),-late)$(NEWLINE)))

$(BUILD_DIR)/packages/rpm/repo-late.done: export UPDATE_REPO:=$(UPDATE_REPO)
	sh -c "$${UPDATE_REPO}"
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/build-late.done: $(BUILD_DIR)/packages/rpm/repo-late.done
	$(ACTION.TOUCH)
