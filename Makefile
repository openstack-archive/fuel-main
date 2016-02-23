.PHONY: clean help

# Path to the sources.
# Default value: directory with Makefile
SOURCE_DIR?=$(dir $(lastword $(MAKEFILE_LIST)))
SOURCE_DIR:=$(abspath $(SOURCE_DIR))
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

CENTOS_MIRROR_YAML?=$(BUILD_DIR)/centos_mirror.yaml
UBUNTU_MIRROR_YAML?=$(BUILD_DIR)/ubuntu_mirror.yaml
CONFIG_YAML?=$(BUILD_DIR)/config.yaml

ISOROOT:=$(BUILD_DIR)/iso/isoroot

include $(SOURCE_DIR)/rules.mk

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

$(BUILD_DIR)/config.yaml.mk: $(CONFIG_YAML)
	mkdir -p $(@D)
	python $(SOURCE_DIR)/evaluator.py \
		-m -c $(CONFIG_YAML) -o $@

$(CONFIG_YAML): $(SOURCE_DIR)/yaml/config.yaml; $(ACTION.COPY)

$(CENTOS_MIRROR_YAML): $(SOURCE_DIR)/yaml/centos_mirror.yaml $(CONFIG_YAML)
	mkdir -p $(@D)
	python $(SOURCE_DIR)/evaluator.py \
		-t $(SOURCE_DIR)/yaml/centos_mirror.yaml \
		-u '{"ISOROOT": "$(ISOROOT)"}' \
		-c $(CONFIG_YAML) \
		-o $@.tmp
	mv $@.tmp $@

$(UBUNTU_MIRROR_YAML): $(SOURCE_DIR)/yaml/ubuntu_mirror.yaml $(CONFIG_YAML)
	mkdir -p $(@D)
	python $(SOURCE_DIR)/evaluator.py \
		-t $(SOURCE_DIR)/yaml/ubuntu_mirror.yaml \
		-u '{"ISOROOT": "$(ISOROOT)"}' \
		-c $(CONFIG_YAML) \
		-o $@.tmp
	mv $@.tmp $@

include $(CONFIG_YAML).mk
include $(SOURCE_DIR)/iso/module.mk
