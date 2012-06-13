
BUILD_DIR:=build

MODULES=gnupg iso2

.PHONY: all clean help

help:
	@echo 'Available targets:'
	@echo '  all - build product'
	@echo '  iso - build nailgun iso'

all:

clean:
	rm -rf $(BUILD_DIR)

include $(addsuffix /module.mk,$(MODULES))

include rules.mk

