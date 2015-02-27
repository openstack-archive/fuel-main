include $(SOURCE_DIR)/packages/rpm/rpm_mock_config.mk

.PHONY: clean clean-rpm

clean: clean-rpm

clean-rpm:
	rm -rf $(BUILD_DIR)/packages/rpm

RPM_SOURCES:=$(BUILD_DIR)/packages/rpm/SOURCES

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
	$(ACTION.TOUCH)

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


$(BUILD_DIR)/packages/rpm/$1.done: \
		$(SOURCE_DIR)/packages/rpm/specs/$1.spec \
		$(BUILD_DIR)/repos/repos.done \
		$(BUILD_DIR)/packages/rpm/mock-config.done
	mkdir -p $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	mkdir -p $(BUILD_DIR)/packages/rpm/SRPMS/x86_64

	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
	-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) --init \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/

########
	# Install centos-release
	# do we need this package?
	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
	-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--install centos-release

	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
	-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/ \
	--shell "rm -f /etc/yum.repos.d/CentOS-*"
#########

	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
		-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) \
		--spec=$(SOURCE_DIR)/packages/rpm/specs/$1.spec \
		--sources=$(BUILD_DIR)/packages/sources/$1/ \
		--buildsrpm \
		--resultdir $(BUILD_DIR)/packages/rpm/SRPMS/x86_64

	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
		-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) \
		--rebuild $(BUILD_DIR)/packages/rpm/SRPMS/x86_64/$1*.src.rpm \
		--resultdir=$(BUILD_DIR)/packages/rpm/RPMS/x86_64/

	$$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/$1-repocleanup.done: $(BUILD_DIR)/mirror/build.done
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
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.src.rpm' -delete;
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/build.done: $(BUILD_DIR)/packages/rpm/repo.done
	$(ACTION.TOUCH)
