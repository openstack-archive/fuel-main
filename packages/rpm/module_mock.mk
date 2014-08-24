include $(SOURCE_DIR)/packages/rpm/mock_config.mk

.PHONY: clean clean-rpm

clean: clean-rpm

clean-rpm:
	rm -rf $(BUILD_DIR)/packages/rpm

RPM_SOURCES:=$(BUILD_DIR)/packages/rpm/SOURCES

# Usage:
# (eval (call prepare_file_source,package_name,file_name,source_path))
define prepare_file_source
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/rpm/sources/$1/$2
$(BUILD_DIR)/packages/rpm/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/rpm/sources/$1
	cp $3 $(BUILD_DIR)/packages/rpm/sources/$1/$2
endef

# Usage:
# (eval (call prepare_python_source,package_name,file_name,source_path))
define prepare_python_source
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/rpm/sources/$1/$2
$(BUILD_DIR)/packages/rpm/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/rpm/sources/$1
ifeq ($1,nailgun)
	cd $3 && npm install && grunt build --static-dir=compressed_static
	rm -rf $3/static
	mv $3/compressed_static $3/static
endif
	cd $3 && python setup.py sdist -d $(BUILD_DIR)/packages/rpm/sources/$1
endef

# Usage:
# (eval (call prepare_tgz_source,package_name,file_name,source_path))
define prepare_tgz_source
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/rpm/sources/$1/$2
$(BUILD_DIR)/packages/rpm/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/rpm/sources/$1
	cd $3 && tar zcf $(BUILD_DIR)/packages/rpm/sources/$1/$2 *
endef

# Usage:
# (eval (call prepare_ruby21_source,package_name,file_name,source_path))
define prepare_ruby21_source
$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/packages/rpm/sources/$1/$2
$(BUILD_DIR)/packages/rpm/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/rpm/sources/$1
	cd $3 && gem build *.gemspec && cp $2 $(BUILD_DIR)/packages/rpm/sources/$1/$2
endef

# main config file, can be empty and options can be passed using command line
$(BUILD_DIR)/packages/rpm/mock/site-defaults.cfg: $(call depv,mock-site-defaults)
$(BUILD_DIR)/packages/rpm/mock/site-defaults.cfg: export contents:=$(mock-site-defaults)
$(BUILD_DIR)/packages/rpm/mock/site-defaults.cfg:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

# mock logging files
$(BUILD_DIR)/packages/rpm/mock/logging.ini: $(call depv,mock-logging)
$(BUILD_DIR)/packages/rpm/mock/logging.ini: export contents:=$(mock-logging)
$(BUILD_DIR)/packages/rpm/mock/logging.ini:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

# main mock file config
$(BUILD_DIR)/packages/rpm/mock/fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH).cfg: $(call depv,mock-fuel-config)
$(BUILD_DIR)/packages/rpm/mock/fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH).cfg: export contents:=$(mock-fuel-config)
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

$(BUILD_DIR)/packages/rpm/$1.done: $(BUILD_DIR)/mirror/build.done

$(BUILD_DIR)/packages/rpm/$1.done: \
		$(SOURCE_DIR)/packages/rpm/specs/$1.spec \
		$(BUILD_DIR)/repos/repos.done \
		$(BUILD_DIR)/packages/rpm/mock-config.done
	mkdir -p $(BUILD_DIR)/packages/rpm/RPMS/x86_64
	mkdir -p $(BUILD_DIR)/packages/rpm/SRPMS/x86_64

	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
	-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) --init \
	--resultdir $(BUILD_DIR)/packages/rpm/RPMS/x86_64/

	/usr/bin/mock --configdir=$(BUILD_DIR)/packages/rpm/mock \
		-r fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH) \
		--spec=$(SOURCE_DIR)/packages/rpm/specs/$1.spec \
		--sources=$(BUILD_DIR)/packages/rpm/sources/$1/ \
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

$(eval $(call prepare_file_source,fencing-agent,fencing-agent.rb,$(BUILD_DIR)/repos/nailgun/bin/fencing-agent.rb))
$(eval $(call prepare_file_source,fencing-agent,fencing-agent.cron,$(BUILD_DIR)/repos/nailgun/bin/fencing-agent.cron))
$(eval $(call prepare_python_source,fuel-ostf,fuel-ostf-0.1.tar.gz,$(BUILD_DIR)/repos/ostf))
$(eval $(call prepare_python_source,fuelmenu,fuelmenu-0.1.tar.gz,$(BUILD_DIR)/repos/nailgun/fuelmenu))
$(eval $(call prepare_file_source,nailgun-agent,agent,$(BUILD_DIR)/repos/nailgun/bin/agent))
$(eval $(call prepare_file_source,nailgun-agent,nailgun-agent.cron,$(BUILD_DIR)/repos/nailgun/bin/nailgun-agent.cron))
$(eval $(call prepare_tgz_source,nailgun-mcagents,mcagents.tar.gz,$(BUILD_DIR)/repos/astute/mcagents))
$(eval $(call prepare_tgz_source,ruby21-nailgun-mcagents,nailgun-mcagents.tar.gz,$(BUILD_DIR)/repos/astute/mcagents))
$(eval $(call prepare_python_source,nailgun-net-check,nailgun-net-check-0.2.tar.gz,$(BUILD_DIR)/repos/nailgun/network_checker))
$(eval $(call prepare_python_source,nailgun,nailgun-0.1.0.tar.gz,$(BUILD_DIR)/repos/nailgun/nailgun))
$(eval $(call prepare_python_source,python-fuelclient,fuelclient-0.2.tar.gz,$(BUILD_DIR)/repos/nailgun/fuelclient))
$(eval $(call prepare_python_source,shotgun,Shotgun-0.1.0.tar.gz,$(BUILD_DIR)/repos/nailgun/shotgun))
$(eval $(call prepare_file_source,nailgun-redhat-license,get_redhat_licenses,$(SOURCE_DIR)/packages/rpm/nailgun-redhat-license/get_redhat_licenses))
$(eval $(call prepare_file_source,ruby21-rubygem-astute,astute.conf,$(SOURCE_DIR)/packages/rpm/astute.conf))
$(eval $(call prepare_ruby21_source,ruby21-rubygem-astute,astute-0.0.2.gem,$(BUILD_DIR)/repos/astute))

$(eval $(call build_rpm,fencing-agent))
$(eval $(call build_rpm,fuelmenu))
$(eval $(call build_rpm,nailgun-mcagents))
$(eval $(call build_rpm,ruby21-nailgun-mcagents))
$(eval $(call build_rpm,nailgun-net-check))
$(eval $(call build_rpm,nailgun))
$(eval $(call build_rpm,shotgun))
$(eval $(call build_rpm,fuel-ostf))
$(eval $(call build_rpm,nailgun-agent))
$(eval $(call build_rpm,nailgun-redhat-license))
$(eval $(call build_rpm,python-fuelclient))
$(eval $(call build_rpm,ruby21-rubygem-astute))

$(BUILD_DIR)/packages/rpm/repo.done:
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.src.rpm' -delete;
	find $(BUILD_DIR)/packages/rpm/RPMS -name '*.rpm' -exec cp -u {} $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \;
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(LOCAL_MIRROR_CENTOS_OS_BASEURL)
	$(ACTION.TOUCH)

$(BUILD_DIR)/packages/rpm/build.done: $(BUILD_DIR)/packages/rpm/repo.done
	$(ACTION.TOUCH)
