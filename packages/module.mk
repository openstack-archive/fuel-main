# Usage:
# (eval (call prepare_file_source,package_name,file_name,source_path))
# Note: dependencies for deb targets are also specified here to make
# sure the source is ready before the build is started.
define prepare_file_source
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/sources/$1
	cp $3 $(BUILD_DIR)/packages/sources/$1/$2
endef

# Usage:
# (eval (call prepare_python_source,package_name,file_name,source_path))
# Note: dependencies for deb targets are also specified here to make
# sure the source is ready before the build is started.
define prepare_python_source
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/sources/$1
ifeq ($1,nailgun)
	mkdir -p $(BUILD_DIR)/npm-cache
	cd $3 && npm --cache $(BUILD_DIR)/npm-cache install && grunt build --static-dir=compressed_static
	rm -rf $3/static
	mv $3/compressed_static $3/static
endif
	cd $3 && python setup.py sdist -d $(BUILD_DIR)/packages/sources/$1
endef

# Usage:
# (eval (call prepare_tgz_source,package_name,file_name,source_path))
# Note: dependencies for deb targets are also specified here to make
# sure the source is ready before the build is started.
define prepare_tgz_source
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/sources/$1
	cd $3 && tar zcf $(BUILD_DIR)/packages/sources/$1/$2 *
endef

# Usage:
# (eval (call prepare_ruby21_source,package_name,file_name,source_path))
# Note: dependencies for deb targets are also specified here to make
# sure the source is ready before the build is started.
define prepare_ruby21_source
$(BUILD_DIR)/packages/sources/$1/$2: $(BUILD_DIR)/repos/repos.done
$(BUILD_DIR)/packages/source_$1.done: $(BUILD_DIR)/packages/sources/$1/$2
$(BUILD_DIR)/packages/sources/$1/$2: $(call find-files,$3)
	mkdir -p $(BUILD_DIR)/packages/sources/$1
	cd $3 && gem build *.gemspec && cp $2 $(BUILD_DIR)/packages/sources/$1/$2
endef

PACKAGE_VERSION=6.0.0
$(BUILD_DIR)/packages/source_%.done:
	$(ACTION.TOUCH)

#NAILGUN_PKGS
$(eval $(call prepare_file_source,fencing-agent,fencing-agent.rb,$(BUILD_DIR)/repos/nailgun/bin/fencing-agent.rb))
$(eval $(call prepare_file_source,fencing-agent,fencing-agent.cron,$(BUILD_DIR)/repos/nailgun/bin/fencing-agent.cron))
$(eval $(call prepare_python_source,fuel-agent,fuel-agent-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/nailgun/fuel_agent))
$(eval $(call prepare_file_source,fuel-agent,fuel-agent.conf,$(BUILD_DIR)/repos/nailgun/fuel_agent/etc/fuel-agent/fuel-agent.conf.sample))
$(eval $(call prepare_tgz_source,fuel-agent,fuel-agent-cloud-init-templates.tar.gz,$(BUILD_DIR)/repos/nailgun/fuel_agent/cloud-init-templates))
$(eval $(call prepare_python_source,fuelmenu,fuelmenu-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/nailgun/fuelmenu))
$(eval $(call prepare_file_source,nailgun-agent,agent,$(BUILD_DIR)/repos/nailgun/bin/agent))
$(eval $(call prepare_file_source,nailgun-agent,nailgun-agent.cron,$(BUILD_DIR)/repos/nailgun/bin/nailgun-agent.cron))
$(eval $(call prepare_python_source,nailgun-net-check,nailgun-net-check-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/nailgun/network_checker))
$(eval $(call prepare_python_source,python-tasklib,tasklib-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/nailgun/tasklib))
$(eval $(call prepare_python_source,nailgun,nailgun-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/nailgun/nailgun))
$(eval $(call prepare_python_source,shotgun,shotgun-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/nailgun/shotgun))
#FUEL_OSTF_PKGS
$(eval $(call prepare_python_source,fuel-ostf,fuel-ostf-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/ostf))
#ASTUTE_PKGS
$(eval $(call prepare_tgz_source,nailgun-mcagents,mcagents.tar.gz,$(BUILD_DIR)/repos/astute/mcagents))
$(eval $(call prepare_tgz_source,ruby21-nailgun-mcagents,nailgun-mcagents.tar.gz,$(BUILD_DIR)/repos/astute/mcagents))
$(eval $(call prepare_ruby21_source,ruby21-rubygem-astute,astute-$(PACKAGE_VERSION).gem,$(BUILD_DIR)/repos/astute))
#FUELLIB_PKGS
$(eval $(call prepare_tgz_source,fuel-library,fuel-library-6.1-6.1-1.tar.gz,$(BUILD_DIR)/repos/fuellib))
#FUEL_PYTHON_PKGS
$(eval $(call prepare_python_source,python-fuelclient,python-fuelclient-$(PACKAGE_VERSION).tar.gz,$(BUILD_DIR)/repos/python-fuelclient))

include $(SOURCE_DIR)/packages/rpm/module.mk
include $(SOURCE_DIR)/packages/deb/module.mk

.PHONY: packages

ifneq ($(BUILD_PACKAGES),0)
$(BUILD_DIR)/packages/build.done: \
		$(BUILD_DIR)/packages/rpm/build.done \
		$(BUILD_DIR)/packages/deb/build.done
endif

$(BUILD_DIR)/packages/build.done:
	$(ACTION.TOUCH)

packages: $(BUILD_DIR)/packages/build.done

packages-deb: $(BUILD_DIR)/packages/deb/build.done
packages-rpm: $(BUILD_DIR)/packages/rpm/build.done
