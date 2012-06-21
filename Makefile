
BUILD_DIR:=build

MODULES=gnupg iso2 test

.PHONY: all clean test help

help:
	@echo 'Available targets:'
	@echo '  all  - build product'
	@echo '  iso  - build nailgun iso'
	@echo '  test - run tests'

all:

test:

clean:
	rm -rf $(BUILD_DIR)

assert-variable=$(if $($1),,$(error Variable $1 need to be defined))

include config.mk

include $(addsuffix /module.mk,$(MODULES))

include rules.mk

