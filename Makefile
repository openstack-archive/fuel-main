
BUILD_DIR:=build

MODULES=gnupg bootstrap nailgun test os os/centos os/ubuntu iso packages/rpm naily

.PHONY: all clean test test-unit help mirror FORCE

help:
	@echo 'Available targets:'
	@echo '  all  - build product'
	@echo '  bootstrap  - build nailgun bootstrap'
	@echo '  iso  - build nailgun iso'
	@echo '  sdist-nailgun - build nailgun sdist'
	@echo '  test - run all tests'
	@echo '  test-unit - run unit tests'
	@echo '  test-integration - run integration tests'
	@echo '  test-cookbooks - run cookbooks tests'
	@echo '  clean-integration-test - clean integration test environment'
	@echo '  clean-cookbooks-test - clean cookbooks test environment'

all:

test: test-unit

test-unit:

ifeq (mirror, $(findstring mirror,$(MAKECMDGOALS)))
ifndef MIRROR_DIR
$(error Please specify MIRROR_DIR variable: make MIRROR_DIR=/path/to/mirror mirror)
else
ifndef IGNORE_MIRROR
IGNORE_MIRROR:=1
endif
endif
endif

# target to force rebuild of other targets
FORCE:

clean:
	rm -rf $(BUILD_DIR)

assert-variable=$(if $($1),,$(error Variable $1 need to be defined))
find-files=$(shell test -d $1 && cd $1 && find * -type f 2> /dev/null)

include config.mk

define include-module-template
MODULE_SOURCE_DIR:=$1
MODULE_BUILD_DIR:=$(BUILD_DIR)/$1
.:=$$(MODULE_SOURCE_DIR)
/:=$$(MODULE_BUILD_DIR)/
$$/%: .:=$$.
$$/%: /:=$$/
include $1/module.mk
endef

include-module=$(eval $(call include-module-template,$1))

$(foreach module,$(MODULES),$(call include-module,$(module)))

include rules.mk

