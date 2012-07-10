
BUILD_DIR:=build

MODULES=gnupg bootstrap iso nailgun test

.PHONY: all clean test test-unit help FORCE

help:
	@echo 'Available targets:'
	@echo '  all  - build product'
	@echo '  bootstrap  - build nailgun bootstrap'
	@echo '  iso  - build nailgun iso'
	@echo '  test - run all tests'
	@echo '  test-unit - run unit tests'
	@echo '  test-integration - run integration tests'
	@echo '  test-cookbooks - run cookbooks tests'
	@echo '  clean-integration-test - clean integration test environment'
	@echo '  clean-cookbooks-test - clean cookbooks test environment'

all:

test: test-unit

test-unit:

# target to force rebuild of other targets
FORCE:

clean:
	rm -rf $(BUILD_DIR)

assert-variable=$(if $($1),,$(error Variable $1 need to be defined))

include config.mk

include $(addsuffix /module.mk,$(MODULES))

include rules.mk

