
BUILD_DIR:=build
/:=$(BUILD_DIR)/

MODULES=

.PHONY: all clean help

help:
	@echo 'Available targets:'
	@echo '  all - build product'

all:

clean:
	rm -rf $(BUILD_DIR)

include $(addsuffix /module.mk,$(MODULES))

include rules.mk

