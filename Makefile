.PHONY: all clean help deep_clean

help:
	@echo 'Build directives (can be overrided by environment variables'
	@echo 'or by command line parameters):'
	@echo '  SOURCE_DIR:       $(SOURCE_DIR)'
	@echo '  BUILD_DIR:        $(BUILD_DIR)'
	@echo '  LOCAL_MIRROR:     $(LOCAL_MIRROR)'
	@echo '  ISO_DIR/ISO_NAME: $(ISO_PATH)'
	@echo
	@echo 'Available targets:'
	@echo '  all  - build product'
	@echo '  iso  - build iso image'
	@echo '  clean - remove build directory and resetting .done flags'
	@echo '  deep_clean - clean + removing $(LOCAL_MIRROR) directory'
	@echo
	@echo 'make iso'
	@echo

# Path to the sources.
# Default value: directory with Makefile
SOURCE_DIR?=$(dir $(lastword $(MAKEFILE_LIST)))
SOURCE_DIR:=$(abspath $(SOURCE_DIR))
# Path to the input data directory
DATA_DIR?=$(SOURCE_DIR)/data
DATA_DIR:=$(abspath $(DATA_DIR))
# Base path for build and mirror directories.
# Default value: current directory
TOP_DIR?=$(PWD)
TOP_DIR:=$(abspath $(TOP_DIR))
# Working build directory
BUILD_DIR?=$(TOP_DIR)/build
BUILD_DIR:=$(abspath $(BUILD_DIR))
# Path for build artifacts
ARTS_DIR?=$(BUILD_DIR)/artifacts
ARTS_DIR:=$(abspath $(ARTS_DIR))
# Path for cache of downloaded packages
LOCAL_MIRROR?=$(TOP_DIR)/local_mirror
LOCAL_MIRROR:=$(abspath $(LOCAL_MIRROR))

all: iso

clean:
	sudo rm -rf $(BUILD_DIR)
deep_clean: clean
	sudo rm -rf $(LOCAL_MIRROR)

vbox-scripts:
	echo "Target is deprecated. Virtualbox scripts have been moved to http://git.openstack.org/openstack/fuel-virtualbox.git"

RPM_REPOS_YAML?=$(DATA_DIR)/rpm_repos.yaml
RPM_PACKAGES_YAML?=$(DATA_DIR)/rpm_packages.yaml
RPM_MOS_REPOS_YAML?=$(DATA_DIR)/rpm_mos_repos.yaml
RPM_MOS_FILTERS_YAML?=$(DATA_DIR)/rpm_mos_filters.yaml
DEB_MOS_REPOS_YAML?=$(DATA_DIR)/deb_mos_repos.yaml
DEB_MOS_FILTERS_YAML?=$(DATA_DIR)/deb_mos_filters.yaml
CONFIG_YAML?=$(DATA_DIR)/config.yaml

define yaml2make
$(BUILD_DIR)/$(notdir $1).mk:
	mkdir -p $$(@D)
	python $(SOURCE_DIR)/evaluator.py -m -c $1 -p $(notfile $1)_ -d 2 -o $$@

include $(BUILD_DIR)/$(notdir $1).mk
endef

$(foreach yaml_file,$(CONFIG_YAML) $(RPM_REPOS_YAML),$(eval $(call yaml2make,$(yaml_file))))

# Macros for make
include $(SOURCE_DIR)/rules.mk

# Modules
include $(SOURCE_DIR)/mirror.mk
include $(SOURCE_DIR)/iso/module.mk
