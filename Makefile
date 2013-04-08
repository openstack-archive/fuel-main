PWD:=$(shell pwd -P)

SOURCE_DIR:=$(PWD)
BUILD_DIR:=$(PWD)/build
DEPV_DIR:=$(BUILD_DIR)/depv

.PHONY: all clean test help deep_clean

help:
	@echo 'Available targets:'
	@echo '  all  - build product'
	@echo '  bootstrap  - build bootstrap'
	@echo '  iso  - build iso image'
	@echo '  img  - build flash stick image'
	@echo '  test - run all tests'
	@echo '  test-unit - run unit tests'
	@echo '  test-integration - run integration tests'
	@echo '  test-integration-env - prepares integration test environment'
	@echo '  clean-integration-test - clean integration test environment'
	@echo '  clean - remove build directory and resetting .done flags'
	@echo '  deep_clean - clean + removing $(LOCAL_MIRROR) directory'
	@echo '  distclean - cleans deep_clean + clean-integration-test'
	@echo
	@echo 'To build system using one of the proprietary mirrors use '
	@echo 'the following commands:'
	@echo
	@echo 'Saratov office (default):'
	@echo 'make iso'
	@echo
	@echo 'Moscow office:'
	@echo 'make iso USE_MIRROR=msk'
	@echo
	@echo 'Custom location:'
	@echo 'make iso USE_MIRROR=msk YUM_REPOS=proprietary \
MIRROR_CENTOS=http://<your_mirror>/centos \
MIRROR_EGGS=http://<your_mirror>/eggs \
MIRROR_GEMS=http://<your_mirror>/gems \
MIRROR_SRC=http://<your_mirror>/src'

all: iso

test: test-unit test-integration

clean:
	sudo rm -rf $(BUILD_DIR)
deep_clean: clean
	sudo rm -rf $(LOCAL_MIRROR)

distclean: deep_clean clean-integration-test

include $(SOURCE_DIR)/rules.mk

# Common configuration file.
include $(SOURCE_DIR)/config.mk

# Sandbox macroses.
include $(SOURCE_DIR)/sandbox.mk

# Modules
include $(SOURCE_DIR)/mirror/module.mk
include $(SOURCE_DIR)/packages/module.mk
include $(SOURCE_DIR)/bootstrap/module.mk
include $(SOURCE_DIR)/iso/module.mk
include $(SOURCE_DIR)/fuelweb_test/module.mk
