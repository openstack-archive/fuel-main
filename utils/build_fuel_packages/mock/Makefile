.PHONY: clean packages packages-deb packages-rpm

help:
	@echo 'Build directives (can be overrided by environment variables'
	@echo 'or by command line parameters):'
	@echo '  SOURCE_PATH:      $(SOURCE_PATH)'
	@echo '  SPEC_FILE_PATH:   $(SPEC_FILE_PATH)'
	@echo '  BUILD_DIR:        $(BUILD_DIR)'
	@echo '  RPM_RESULT_DIR:   $(RPM_RESULT_DIR)'


# Default value: current directory
TOP_DIR?=$(PWD)
TOP_DIR:=$(abspath $(TOP_DIR))

# Path to the sources.
# Default value: directory with Makefile
SOURCE_DIR?=$(dir $(lastword $(MAKEFILE_LIST)))
SOURCE_DIR:=$(abspath $(SOURCE_DIR))

# Working build directory
BUILD_DIR?=$(TOP_DIR)/build
BUILD_DIR:=$(abspath $(BUILD_DIR))
RPM_RESULT_DIR?=$(BUILD_DIR)/rpm

PRODUCT_VERSION:=7.0

SOURCE_PATH?=$(HOME)/test/fuel-main/build/packages/sources
SPEC_FILE_PATH?=$(HOME)/test/fuel-main/build/repos
UID?=$(shell id -u)

RPM_PACKAGES_TO_BUILD:=\
astute \
fuel-library$(PRODUCT_VERSION) \
fuel-main \
fuel-ostf \
nailgun \
python-fuelclient

# Macroses for make
define ACTION.TOUCH
@mkdir -p $(@D)
touch $@
endef


clean:
	rm -rf $(BUILD_DIR)

# Usage:
# (eval (call build_rpm,package_name))
define build_rpm

# You can use package name as a target, for example: make nailgun
# It will build nailgun related rpm package
$1: $(BUILD_DIR)/$1.done

$(BUILD_DIR)/config/fuel-$(PRODUCT_VERSION)-$1.cfg:
	@mkdir -p $$(@D)
	cp -u $(SOURCE_DIR)/configs/site-defaults.cfg $$(@D)
	cp -u $(SOURCE_DIR)/configs/logging.ini $$(@D)
	sed 's/@@PACKAGE@@/$1/g' $(SOURCE_DIR)/configs/mock-template.cfg > $$@


$(BUILD_DIR)/$1.done: $(BUILD_DIR)/config/fuel-$(PRODUCT_VERSION)-$1.cfg
	mkdir -p $(RPM_RESULT_DIR)
	/usr/bin/mock -v --configdir=$(BUILD_DIR)/config/ \
	-r fuel-$(PRODUCT_VERSION)-$1 --init \
	--resultdir $(RPM_RESULT_DIR)

	/usr/bin/mock -v --configdir=$(BUILD_DIR)/config/ \
		-r fuel-$(PRODUCT_VERSION)-$1 \
		--spec=$(SPEC_FILE_PATH)/$1/specs/$1.spec \
		--sources=$(SOURCE_PATH)/$1/ \
		--buildsrpm \
		--resultdir $(RPM_RESULT_DIR)/$1/

	/usr/bin/mock -v --configdir=$(BUILD_DIR)/config/ \
		-r fuel-$(PRODUCT_VERSION)-$1 \
		--rebuild $(RPM_RESULT_DIR)/$1/*.src.rpm \
		--resultdir $(RPM_RESULT_DIR)

	$$(ACTION.TOUCH)

endef


packages: $(RPM_PACKAGES_TO_BUILD:%=$(BUILD_DIR)/%.done)

$(eval $(foreach pkg,$(RPM_PACKAGES_TO_BUILD),$(call build_rpm,$(pkg))))
