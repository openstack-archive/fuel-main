
BUILD_DIR:=build
/:=$(BUILD_DIR)/

MODULES=

.PHONY: all clean help

help:
	@echo 'Available targets:'
	@echo '  all - build product'
	@echo '  install-prerequisites - install all external prerequisistes'

all:

clean:
	rm -rf $(BUILD_DIR)

include $(addsuffix /module.mk,$(MODULES))

include rules.mk
include prerequisites.mk

