include $(SOURCE_DIR)/packages/openstack/rpm/mock_config.mk


# prepare config files for mock, wich defined in mock_config.mk
$(BUILD_DIR)/openstack/rpm/mock/site-defaults.cfg: $(call depv,openstack-mock-site-defaults)
$(BUILD_DIR)/openstack/rpm/mock/site-defaults.cfg: export contents:=$(openstack-mock-site-defaults)
$(BUILD_DIR)/openstack/rpm/mock/site-defaults.cfg:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

# mock logging files
$(BUILD_DIR)/openstack/rpm/mock/logging.ini: $(call depv,openstack-mock-logging)
$(BUILD_DIR)/openstack/rpm/mock/logging.ini: export contents:=$(openstack-mock-logging)
$(BUILD_DIR)/openstack/rpm/mock/logging.ini:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

# main mock file config
$(BUILD_DIR)/openstack/rpm/mock/fuel-$(PRODUCT_VERSION)-openstack-$(CENTOS_ARCH).cfg: $(call depv,openstack-mock-fuel-config)
$(BUILD_DIR)/openstack/rpm/mock/fuel-$(PRODUCT_VERSION)-openstack-$(CENTOS_ARCH).cfg: export contents:=$(openstack-mock-fuel-config)
$(BUILD_DIR)/openstack/rpm/mock/fuel-$(PRODUCT_VERSION)-openstack-$(CENTOS_ARCH).cfg:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

# let's provide all targets (we need the below configs) for running mock
$(BUILD_DIR)/openstack/rpm/mock-config.done: \
		$(BUILD_DIR)/openstack/rpm/mock/site-defaults.cfg \
		$(BUILD_DIR)/openstack/rpm/mock/logging.ini \
		$(BUILD_DIR)/openstack/rpm/mock/fuel-$(PRODUCT_VERSION)-openstack-$(CENTOS_ARCH).cfg
	$(ACTION.TOUCH)


# Usage:
# (eval (call prepare_openstack_source,package_name,file_name,source_path))
define prepare_openstack_source
$(BUILD_DIR)/openstack/rpm/$1.done: $(BUILD_DIR)/openstack/rpm/sources/$1/$2
$(BUILD_DIR)/openstack/rpm/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/openstack/rpm/sources/$1
	cd $3 && python setup.py sdist -d $(BUILD_DIR)/openstack/rpm/sources/$1 && python setup.py --version sdist > $(BUILD_DIR)/openstack/rpm/$1-version-tag
endef

# Usage:
# (eval (call build_openstack_rpm,package_name))
define build_openstack_rpm
$(BUILD_DIR)/openstack/rpm/repo.done: $(BUILD_DIR)/openstack/rpm/$1.done
$(BUILD_DIR)/openstack/rpm/repo.done: $(BUILD_DIR)/openstack/rpm/$1-repocleanup.done

# You can use package name as a target, for example: make neutron
# It will build neutron rpm package
$1: $(BUILD_DIR)/openstack/rpm/$1.done

$(BUILD_DIR)/openstack/rpm/$1.done: $(BUILD_DIR)/mirror/build.done

$(BUILD_DIR)/openstack/rpm/$1.done: \
	$(BUILD_DIR)/repos/repos.done \
	$(BUILD_DIR)/openstack/rpm/mock-config.done

	mkdir -p $(BUILD_DIR)/openstack/rpm/RPMS/x86_64
	mkdir -p $(BUILD_DIR)/openstack/rpm/SRPMS/x86_64
	mkdir -p $(BUILD_DIR)/openstack/rpm/sources/specs

	/usr/bin/mock --configdir=$(BUILD_DIR)/openstack/rpm/mock \
	-r fuel-$(PRODUCT_VERSION)-openstack-$(CENTOS_ARCH) --init \
	--resultdir $(BUILD_DIR)/openstack/rpm/RPMS/x86_64/

# gathering sources in one place
	cp -r $(BUILD_DIR)/repos/$1-build/rpm/SOURCES/* $(BUILD_DIR)/openstack/rpm/sources/$1

	sed "s/Version:.*/Version:\t`cat $(BUILD_DIR)/openstack/rpm/$1-version-tag`/" $(BUILD_DIR)/repos/$1-build/rpm/SPECS/*.spec > $(BUILD_DIR)/openstack/rpm/sources/specs/openstack-$1.spec
	sed -i "s/Source0:.*/Source0:\t$1-`cat $(BUILD_DIR)/openstack/rpm/$1-version-tag`\.tar\.gz/" $(BUILD_DIR)/openstack/rpm/sources/specs/openstack-$1.spec

	/usr/bin/mock --configdir=$(BUILD_DIR)/openstack/rpm/mock \
		-r fuel-$(PRODUCT_VERSION)-openstack-$(CENTOS_ARCH) \
		--spec=$(BUILD_DIR)/openstack/rpm/sources/specs/openstack-$1.spec \
		--sources=$(BUILD_DIR)/openstack/rpm/sources/$1/ \
		--resultdir $(BUILD_DIR)/openstack/rpm/SRPMS/x86_64 \
		--buildsrpm \
		--no-cleanup-after

	/usr/bin/mock --configdir=$(BUILD_DIR)/openstack/rpm/mock \
		-r fuel-$(PRODUCT_VERSION)-openstack-$(CENTOS_ARCH) \
		--installdeps $(BUILD_DIR)/openstack/rpm/SRPMS/x86_64/openstack-$1*.src.rpm \
		--resultdir $(BUILD_DIR)/openstack/rpm/SRPMS/x86_64

	/usr/bin/mock --configdir=$(BUILD_DIR)/openstack/rpm/mock \
		-r fuel-$(PRODUCT_VERSION)-openstack-$(CENTOS_ARCH) \
		--rebuild $(BUILD_DIR)/openstack/rpm/SRPMS/x86_64/openstack-$1*.src.rpm \
		--resultdir=$(BUILD_DIR)/openstack/rpm/RPMS/x86_64/


	# sudo createrepo $$(SANDBOX)/tmp/RPMS/noarch/
	# sudo yumdownloader --resolve -c $$(SANDBOX)/etc/yum.conf --enablerepo=centos --enablerepo=centos-master --enablerepo=openstack-local --destdir=$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages openstack-$1* | grep -v '^looking for' | tee $(BUILD_DIR)/openstack/yumdownloader.log
	# sudo sh -c "$$$${SANDBOX_DOWN}"
	$$(ACTION.TOUCH)

$(BUILD_DIR)/openstack/rpm/$1-repocleanup.done: $(BUILD_DIR)/mirror/build.done
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages -regex '.*$1-[^-]+-[^-]+.*' -delete
	$$(ACTION.TOUCH)
endef

ifneq ($(BUILD_OPENSTACK_PACKAGES),0)
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call set_vars,$(pkg))))
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call build_repo,$(pkg),$($(call uc,$(pkg))_REPO),$($(call uc,$(pkg))_COMMIT),$($(call uc,$(pkg))_GERRIT_URL),$($(call uc,$(pkg))_GERRIT_COMMIT))))
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call build_repo,$(pkg)-build,$($(call uc,$(pkg))_SPEC_REPO),$($(call uc,$(pkg))_SPEC_COMMIT),$($(call uc,$(pkg))_SPEC_GERRIT_URL),$($(call uc,$(pkg))_SPEC_GERRIT_COMMIT))))
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call prepare_openstack_source,$(pkg),$(pkg)-2014.1.tar.gz,$(BUILD_DIR)/repos/$(pkg))))
$(foreach pkg,$(subst $(comma), ,$(BUILD_OPENSTACK_PACKAGES)),$(eval $(call build_openstack_rpm,$(pkg))))
endif

$(BUILD_DIR)/openstack/rpm/repo.done:
	find $(BUILD_DIR)/openstack/rpm/RPMS -name '*.src.rpm' -delete;
	find $(BUILD_DIR)/openstack/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

$(BUILD_DIR)/openstack/rpm/build.done: $(BUILD_DIR)/openstack/rpm/repo.done
	$(ACTION.TOUCH)
