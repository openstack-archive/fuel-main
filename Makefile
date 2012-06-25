
BUILD_DIR:=build

MODULES=gnupg bootstrap iso2 test

.PHONY: all clean test help FORCE

help:
	@echo 'Available targets:'
	@echo '  all  - build product'
	@echo '  bootstrap  - build nailgun bootstrap'
	@echo '  iso  - build nailgun iso'
	@echo '  test - run tests'

all:

test:

# target to force rebuild of other targets
FORCE:

clean:
	rm -rf $(BUILD_DIR)

assert-variable=$(if $($1),,$(error Variable $1 need to be defined))

include config.mk

include $(addsuffix /module.mk,$(MODULES))

include rules.mk

