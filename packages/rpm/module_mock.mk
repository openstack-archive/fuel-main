include $(SOURCE_DIR)/packages/rpm/module_mock_config.mk

# main mock config file, can be empty and/or options can be passed using command line
$(BUILD_DIR)/packages/rpm/mock/site-defaults.cfg: $(call depv,rpm-mock-default)
$(BUILD_DIR)/packages/rpm/mock/site-defaults.cfg: export contents:=$(rpm-mock-default)
$(BUILD_DIR)/packages/rpm/mock/site-defaults.cfg:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

# mock logging files
$(BUILD_DIR)/packages/rpm/mock/logging.ini: $(call depv,rpm-mock-logging)
$(BUILD_DIR)/packages/rpm/mock/logging.ini: export contents:=$(rpm-mock-logging)
$(BUILD_DIR)/packages/rpm/mock/logging.ini:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

# main mock file config
ifeq ($(USE_MOCK_WITH_LOCAL_MIRROR),0)
$(BUILD_DIR)/packages/rpm/mock/fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH).cfg: MOCK_MIRROR_CENTOS_OS_BASEURL:=$(MIRROR_CENTOS_OS_BASEURL)
else
$(BUILD_DIR)/packages/rpm/mock/fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH).cfg: MOCK_MIRROR_CENTOS_OS_BASEURL:=file://$(LOCAL_MIRROR_CENTOS_OS_BASEURL)
endif
$(BUILD_DIR)/packages/rpm/mock/fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH).cfg: $(call depv,rpm-mock-config)
$(BUILD_DIR)/packages/rpm/mock/fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH).cfg: export contents:=$(rpm-mock-config)
$(BUILD_DIR)/packages/rpm/mock/fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH).cfg:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

# let's provide all targets for running mock
$(BUILD_DIR)/packages/rpm/mock-config.done: \
		$(BUILD_DIR)/packages/rpm/mock/site-defaults.cfg \
		$(BUILD_DIR)/packages/rpm/mock/logging.ini \
		$(BUILD_DIR)/packages/rpm/mock/fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH).cfg

	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
	-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) --init --no-cleanup-after \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/

	# Install centos-release
	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
	-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) --no-clean --no-cleanup-after \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--install centos-release

	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
	-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) --no-clean --no-cleanup-after \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--shell "rm -f /etc/yum.repos.d/CentOS-*"

	$(ACTION.TOUCH)

# Usage:
# (eval (call build_rpm_in_mock,package_name))
define build_rpm_in_mock
$(BUILD_DIR)/packages/rpm/repo.done: $(BUILD_DIR)/packages/rpm/$1.done
ifeq ($(USE_MOCK_WITH_LOCAL_MIRROR),1)
$(BUILD_DIR)/packages/rpm/repo.done: $(BUILD_DIR)/packages/rpm/$1-repocleanup.done
endif

# You can use package name as a target, for example: make ruby21-rubygem-astute
# It will build astute rpm package
$1: $(BUILD_DIR)/packages/rpm/$1.done

ifeq ($(USE_MOCK_WITH_LOCAL_MIRROR),1)
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/mirror/centos/repo.done
endif
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/source_$1.done


$(BUILD_DIR)/packages/rpm/$1.done: \
		$(SOURCE_DIR)/packages/rpm/specs/$1.spec \
		$(BUILD_DIR)/repos/repos.done \
		$(BUILD_DIR)/packages/rpm/mock-config.done
	mkdir -p $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	mkdir -p $(BUILD_DIR)/packages/rpm/SRPMS/x86_64

	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
		-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) --no-clean --no-cleanup-after \
		--spec=$(SOURCE_DIR)/packages/rpm/specs/$1.spec \
		--sources=$(BUILD_DIR)/packages/sources/$1/ \
		--buildsrpm \
		--resultdir $(BUILD_DIR)/packages/rpm/SRPMS/x86_64

	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
		-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) --no-clean --no-cleanup-after \
		--rebuild $(BUILD_DIR)/packages/rpm/SRPMS/x86_64/$1*.src.rpm \
		--resultdir=$(BUILD_DIR)/packages/rpm/RPMS/x86_64/

	$$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: $(BUILD_DIR)/mirror/build.done
	find $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages -regex '.*/$1-[^-]+-[^-]+' -delete
	$$(ACTION.TOUCH)
endef

$(BUILD_DIR)/packages/rpm/repo.done:
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.src.rpm' -delete
ifeq ($(USE_MOCK_WITH_LOCAL_MIRROR),1)
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)
else
	$(ACTION.TOUCH)
endif
