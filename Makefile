.PHONY: clean help

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

RPM_REPOS_YAML?=$(DATA_DIR)/rpm_repos.yaml
RPM_PACKAGES_YAML?=$(DATA_DIR)/rpm_packages.yaml
RPM_MOS_REPOS_YAML?=$(DATA_DIR)/rpm_mos_repos.yaml
RPM_MOS_FILTERS_YAML?=$(DATA_DIR)/rpm_mos_filters.yaml
DEB_MOS_REPOS_YAML?=$(DATA_DIR)/deb_mos_repos.yaml
DEB_MOS_FILTERS_YAML?=$(DATA_DIR)/deb_mos_filters.yaml
CONFIG_YAML?=$(DATA_DIR)/config.yaml

help:
	@echo 'Build directives (can be overrided by environment variables'
	@echo 'or by command line parameters):'
	@echo '  SOURCE_DIR:       $(SOURCE_DIR)'
	@echo '  BUILD_DIR:        $(BUILD_DIR)'
	@echo
	@echo 'Available targets:'
	@echo '  all  - build product'
	@echo '  iso  - build iso image'
	@echo '  clean - remove build directory and resetting .done flags'
	@echo
	@echo 'Example:'
	@echo '  make iso'

clean:
	sudo rm -rf $(BUILD_DIR)

$(BUILD_DIR)/config.yaml.mk:
	mkdir -p $(@D)
	python $(SOURCE_DIR)/evaluator.py \
		-m -c $(CONFIG_YAML) -o $@

$(BUILD_DIR)/rpm_repos.yaml.mk:
	mkdir -p $(@D)
	python $(SOURCE_DIR)/evaluator.py \
		-m -c $(RPM_REPOS_YAML) \
		-p $(notdir $(RPM_REPOS_YAML))_ -o $@

include $(BUILD_DIR)/config.yaml.mk
include $(BUILD_DIR)/rpm_repos.yaml.mk

include $(SOURCE_DIR)/rules.mk
include $(SOURCE_DIR)/iso/module.mk
