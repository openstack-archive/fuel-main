.PHONY: clean packages packages-deb packages-rpm

help:
	@echo 'Build directives (can be overrided by environment variables'
	@echo 'or by command line parameters):'
	@echo '  SOURCE_PATH:      $(SOURCE_PATH)'
	@echo '  SPEC_FILE_PATH:   $(SPEC_FILE_PATH)'
	@echo '  UID:              $(UID)'
	@echo '  BUILD_DIR:        $(BUILD_DIR)'
	@echo '  DEB_RESULT_DIR:   $(DEB_RESULT_DIR)'
	@echo '  RPM_RESULT_DIR:   $(RPM_RESULT_DIR)'


# Default value: current directory
TOP_DIR?=$(PWD)
TOP_DIR:=$(abspath $(TOP_DIR))
# Working build directory
BUILD_DIR?=$(TOP_DIR)/build
BUILD_DIR:=$(abspath $(BUILD_DIR))
DEB_RESULT_DIR?=$(BUILD_DIR)/deb
RPM_RESULT_DIR?=$(BUILD_DIR)/rpm

SOURCE_PATH?=$(HOME)/test/fuel-main/build/packages/sources
SPEC_FILE_PATH?=$(HOME)/test/fuel-main/build/repos
UID?=$(shell id -u)

RPM_PACKAGES_TO_BUILD:=\
astute \
fuel-library7.0 \
fuel-main \
fuel-ostf \
nailgun \
python-fuelclient

DEB_PACKAGES_TO_BUILD:=\
astute \
fuel-library7.0 \
nailgun

define ACTION.TOUCH
@mkdir -p $(@D)
touch $@
endef

# Usage:
# (eval (call build_rpm,package_name))
define build_rpm

# You can use package name as a target, for example: make nailgun
# It will build nailgun related rpm package
$1: $(BUILD_DIR)/$1.rpm.done

$(BUILD_DIR)/$1.rpm.done:
	mkdir -p $(RPM_RESULT_DIR)
	docker run --privileged --rm -v $(SOURCE_PATH)/$1:/opt/sandbox/SOURCES \
		-v $(SPEC_FILE_PATH)/$1/specs/$1.spec:/opt/sandbox/$1.spec \
		-v $(RPM_RESULT_DIR):/opt/sandbox/RPMS \
		-u $(UID) \
		fuel/rpmbuild_env /bin/bash /opt/sandbox/build_rpm_in_docker.sh
	$$(ACTION.TOUCH)

endef

# Usage:
# (eval (call build_deb,package_name))
define build_deb

# You can use package name as a target, for example: make nailgun
# It will build nailgun related deb package
$1: $(BUILD_DIR)/$1.deb.done

$(BUILD_DIR)/$1.deb.done:
	mkdir -p $(DEB_RESULT_DIR)
	docker run --rm -v $(SOURCE_PATH)/$1:/opt/sandbox/SOURCES \
		-v $(DEB_RESULT_DIR):/opt/sandbox/DEB \
		-u $(UID) \
		fuel/debbuild_env /bin/bash /opt/sandbox/build_deb_in_docker.sh
	$$(ACTION.TOUCH)

endef

clean:
	rm -rf $(BUILD_DIR)

packages: packages-deb packages-rpm

packages-deb: $(DEB_PACKAGES_TO_BUILD:%=$(BUILD_DIR)/%.deb.done)

packages-rpm: $(RPM_PACKAGES_TO_BUILD:%=$(BUILD_DIR)/%.rpm.done)

$(eval $(foreach pkg,$(RPM_PACKAGES_TO_BUILD),$(call build_rpm,$(pkg))))
$(eval $(foreach pkg,$(DEB_PACKAGES_TO_BUILD),$(call build_deb,$(pkg))))
