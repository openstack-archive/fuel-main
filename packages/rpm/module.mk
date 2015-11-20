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

$(BUILD_DIR)/packages/rpm/buildd.tar.gz: SANDBOX_PACKAGES:=rpm-build tar yum yum-utils
$(BUILD_DIR)/packages/rpm/buildd.tar.gz: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX/buildd
$(BUILD_DIR)/packages/rpm/buildd.tar.gz: export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/packages/rpm/buildd.tar.gz: export SANDBOX_DOWN:=$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/buildd.tar.gz: $(BUILD_DIR)/mirror/centos/repo.done \
	$(BUILD_DIR)/mirror/centos/mos-repo.done
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
$1-rpm: $(BUILD_DIR)/packages/rpm/$1.done

$(BUILD_DIR)/packages/rpm/$1.done: SANDBOX:=$(BUILD_DIR)/packages/rpm/SANDBOX/$1
$(BUILD_DIR)/packages/rpm/$1.done: export SANDBOX_DOWN:=$$(SANDBOX_DOWN)
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/source_$1.done
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/rpm/buildd.tar.gz

ifneq (late,$(findstring late,$2))
$(BUILD_DIR)/packages/rpm/$1.done: SPECFILE:=$(BUILD_DIR)/repos/$1/specs/$1.spec
$(BUILD_DIR)/repos/$1/specs/$1.spec: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/repos/$1/specs/$1.spec: $(BUILD_DIR)/repos/$1.done
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/repos/$1/specs/$1.spec
else
$(BUILD_DIR)/packages/rpm/$1.done: SPECFILE:=$(SOURCE_DIR)/packages/rpm/specs/$1.spec
endif

$(BUILD_DIR)/packages/rpm/$1.done:
	mkdir -p $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	mkdir -p $$(SANDBOX) && \
	sudo tar xzf $(BUILD_DIR)/packages/rpm/buildd.tar.gz -C $$(SANDBOX) && \
	sudo chroot $$(SANDBOX) bash -c "(mkdir -p '$$$${TEMP}'; mkdir -p /tmp/user/0)"
	sudo mount --bind /proc $$(SANDBOX)/proc && \
	sudo mount --bind /dev $$(SANDBOX)/dev && \
	mkdir -p $$(SANDBOX)/tmp/SOURCES && \
	sudo cp -r $(BUILD_DIR)/packages/sources/$1/* $$(SANDBOX)/tmp/SOURCES && \
	sudo cp $$(SPECFILE) $$(SANDBOX)/tmp && \
	sudo /bin/sh -c 'export TMPDIR=$$(SANDBOX)/tmp/yum TMP=$$(SANDBOX)/tmp/yum; yum-builddep -y -c $$(SANDBOX)/etc/yum.conf --installroot=$$(SANDBOX) $$(SANDBOX)/tmp/$1.spec'
	test -f $$(SANDBOX)/tmp/SOURCES/version && \
		sudo chroot $$(SANDBOX) rpmbuild --nodeps --define "_topdir /tmp" --define "release `awk -F'=' '/RELEASE/ {print $$$$2}' $$(SANDBOX)/tmp/SOURCES/version`" -ba /tmp/$1.spec || \
		sudo chroot $$(SANDBOX) rpmbuild --nodeps --define "_topdir /tmp" -ba /tmp/$1.spec
	cp $$(SANDBOX)/tmp/RPMS/*/*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	sudo sh -c "$$$${SANDBOX_DOWN}"
	$$(ACTION.TOUCH)

ifneq (late,$(findstring late,$2))
$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: SPECFILE:=$(BUILD_DIR)/repos/$1/specs/$1.spec
$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: $(BUILD_DIR)/packages/source_$1.done
else
$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: SPECFILE:=$(SOURCE_DIR)/packages/rpm/specs/$1.spec
endif
$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: $(BUILD_DIR)/mirror/centos/mos-repo.done
	python $(SOURCE_DIR)/packages/rpm/genpkgnames.py $$(SPECFILE) | xargs -I{} sudo find $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL)/Packages -regex '.*/{}-[^-]+-[^-]+' -delete
	$$(ACTION.TOUCH)
endef


packages_list:=\
astute \
fuel-agent \
fuel-createmirror \
fuel-library$(PRODUCT_VERSION) \
fuel-main \
fuelmenu \
fuel-nailgun \
fuel-nailgun-agent \
fuel-ostf \
network-checker \
python-fuelclient \
shotgun

$(eval $(foreach pkg,$(packages_list),$(call build_rpm,$(pkg))$(NEWLINE)))

$(BUILD_DIR)/packages/rpm/repo.done: $(BUILD_DIR)/bootstrap/fuel-bootstrap-image-builder-rpm.done
$(BUILD_DIR)/packages/rpm/repo.done:
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_MOS_CENTOS)/comps.xml \
		-u media://`head -1 $(SOURCE_DIR)/iso/.discinfo` \
		-o $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

# in case BUILD_PACKAGES=0 we have to build only fuel-bootstrap-image-builder
ifeq (1,$(strip $(BUILD_PACKAGES)))
$(BUILD_DIR)/packages/rpm/build.done: $(BUILD_DIR)/packages/rpm/repo.done
else
$(BUILD_DIR)/packages/rpm/build.done: $(BUILD_DIR)/bootstrap/fuel-bootstrap-image-builder-rpm.done \
		$(BUILD_DIR)/mirror/centos/repo.done
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL)/comps.xml \
	-o $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL)
endif
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
# NOTE(kozhukalov): We don't need target centos images in 8.0
# fuel-target-centos-images$(CENTOS_RELEASE)

$(eval $(foreach pkg,$(fuel_rpm_packages_late),$(call build_rpm,$(pkg),-late)$(NEWLINE)))

$(BUILD_DIR)/packages/rpm/repo.done: $(BUILD_DIR)/bootstrap/fuel-bootstrap-image-builder-rpm.done
# BUILD_PACKAGES=0 - for late packages we need to be sure that centos mirror is ready
# BUILD_PACKAGES=1 - for late packages we need to be sure that fuel-* packages was build beforehand
$(BUILD_DIR)/packages/rpm/repo-late.done: $(BUILD_DIR)/mirror/centos/repo.done
ifeq (1,$(strip $(BUILD_PACKAGES)))
$(BUILD_DIR)/packages/rpm/repo-late.done: $(BUILD_DIR)/packages/rpm/repo.done
endif
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u --target-directory $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL)/Packages {} +
	createrepo -g $(LOCAL_MIRROR_MOS_CENTOS)/comps.xml \
		-u media://`head -1 $(SOURCE_DIR)/iso/.discinfo` \
		-o $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/build-late.done: $(BUILD_DIR)/packages/rpm/repo-late.done
	$(ACTION.TOUCH)
