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

$(BUILD_DIR)/packages/rpm/buildd.tar.gz: SANDBOX_PACKAGES:=ruby rpm-build tar python-setuptools python-pbr nodejs npm yum yum-utils git 
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
	sudo /bin/sh -c 'export TMPDIR=$$(SANDBOX)/tmp/yum TMP=$$(SANDBOX)/tmp/yum; yum-builddep -y -c $$(SANDBOX)/etc/yum.conf --installroot=$$(SANDBOX) $$(SANDBOX)/tmp/$1.spec' && \
	sudo chroot $$(SANDBOX) rpmbuild --nodeps -vv --define "_topdir /tmp" -ba /tmp/$1.spec
	cp $$(SANDBOX)/tmp/RPMS/*/*.rpm $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	sudo sh -c "$$$${SANDBOX_DOWN}"
	$$(ACTION.TOUCH)

ifneq (late,$(findstring late,$2))
$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: SPECFILE:=$(BUILD_DIR)/repos/$1/specs/$1.spec
$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: $(BUILD_DIR)/packages/source_$1.done
else
$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: SPECFILE:=$(SOURCE_DIR)/packages/rpm/specs/$1.spec
endif
$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: $(BUILD_DIR)/mirror/centos/repo.done
	python $(SOURCE_DIR)/packages/rpm/genpkgnames.py $$(SPECFILE) | xargs -I{} sudo find $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages -regex '.*/{}-[^-]+-[^-]+' -delete
	$$(ACTION.TOUCH)
endef


packages_list:=\
fuel-main \
fuel-library$(PRODUCT_VERSION) \
astute \
nailgun \
fuel-ostf \
python-fuelclient 

$(eval $(foreach pkg,$(packages_list),$(call build_rpm,$(pkg))$(NEWLINE)))

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

$(BUILD_DIR)/docker/build.done: $(BUILD_DIR)/packages/rpm/repo-late.done

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
fuel-bootstrap-image \
fuel-target-centos-images

$(eval $(foreach pkg,$(fuel_rpm_packages_late),$(call build_rpm,$(pkg),-late)$(NEWLINE)))

$(BUILD_DIR)/packages/rpm/repo-late.done: $(BUILD_DIR)/packages/rpm/repo.done
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u --target-directory $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages {} +
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/build-late.done: $(BUILD_DIR)/packages/rpm/repo-late.done
	$(ACTION.TOUCH)
