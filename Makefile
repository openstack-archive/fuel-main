PWD:=$(shell pwd -P)

SOURCE_DIR:=$(PWD)
BUILD_DIR:=$(PWD)/build

include $(SOURCE_DIR)/config.mk
include $(SOURCE_DIR)/mirror/module.mk
include $(SOURCE_DIR)/packages/module.mk
include $(SOURCE_DIR)/bootstrap/module.mk
include $(SOURCE_DIR)/iso/module.mk

# MODULES=gnupg bootstrap nailgun test mirror iso packages/rpm naily astute

.PHONY:

# .PHONY: all clean test test-unit help mirror FORCE deep_clean


# help:
# 	@echo 'Available targets:'
# 	@echo '  all  - build product'
# 	@echo '  bootstrap  - build nailgun bootstrap'
# 	@echo '  iso  - build nailgun iso'
# 	@echo '  sdist-nailgun - build nailgun sdist'
# 	@echo '  test - run all tests'
# 	@echo '  test-unit - run unit tests'
# 	@echo '  test-integration - run integration tests'
# 	@echo '  test-cookbooks - run cookbooks tests'
# 	@echo '  clean-integration-test - clean integration test environment'
# 	@echo '  clean-cookbooks-test - clean cookbooks test environment'
# 	@echo '  clean - remove build directory and resetting .done flags'
# 	@echo '  deep_clean - clean + removing $(LOCAL_MIRROR) directory'

# all:

# test: test-unit

# test-unit:

# # target to force rebuild of other targets
# FORCE:

# clean:
# 	rm -rf $(BUILD_DIR)
# 	test -d $(LOCAL_MIRROR) && find $(LOCAL_MIRROR) -name "*.done" -delete
# deep_clean: clean
# 	rm -rf $(LOCAL_MIRROR)

# distclean: deep_clean clean-integration-test

include $(SOURCE_DIR)/rules.mk
