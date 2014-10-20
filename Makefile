.PHONY: all clean help deep_clean

help:
	@echo 'Build directives (can be overrided by environment variables'
	@echo 'or by command line parameters):'
	@echo '  SOURCE_DIR:       $(SOURCE_DIR)'
	@echo '  BUILD_DIR:        $(BUILD_DIR)'
	@echo '  LOCAL_MIRROR:     $(LOCAL_MIRROR)'
	@echo '  EXTRA_RPM_REPOS:  $(EXTRA_RPM_REPOS)'
	@echo '  EXTRA_DEB_REPOS:  $(EXTRA_DEB_REPOS)'
	@echo '  KSYAML:           $(KSYAML)'
	@echo
	@echo 'Available targets:'
	@echo '  all  - build product'
	@echo '  bootstrap  - build bootstrap'
	@echo '  mirror  - build local mirror'
	@echo '  iso  - build iso image'
	@echo '  img  - build flash stick image'
	@echo '  clean - remove build directory and reset .done flags'
	@echo '  deep_clean - clean + remove $(LOCAL_MIRROR) directory'
	@echo
	@echo 'Extra RPM repos:'
	@echo 'make iso EXTRA_RPM_REPOS="<repo1_name>,http://<repo1> <repo2_name>,ftp://<repo2>"'
	@echo
	@echo 'Extra DEB repos:'
	@echo 'make iso EXTRA_DEB_REPOS="http://<repo1>/ubuntu /|ftp://<repo2> precise main"'
	@echo

# Path to the sources.
# Default value: directory with Makefile
SOURCE_DIR?=$(dir $(lastword $(MAKEFILE_LIST)))
SOURCE_DIR:=$(abspath $(SOURCE_DIR))

all: iso

clean:
	sudo rm -rf $(BUILD_DIR)
deep_clean: clean
	sudo rm -rf $(LOCAL_MIRROR)

# Common configuration file.
include $(SOURCE_DIR)/config.mk

# Macroses for make
include $(SOURCE_DIR)/rules.mk

# Sandbox macroses.
include $(SOURCE_DIR)/sandbox.mk

# Modules
include $(SOURCE_DIR)/repos.mk
include $(SOURCE_DIR)/mirror/module.mk
include $(SOURCE_DIR)/puppet/module.mk
include $(SOURCE_DIR)/packages/module.mk
include $(SOURCE_DIR)/packages/openstack/module.mk
include $(SOURCE_DIR)/docker/module.mk
include $(SOURCE_DIR)/bootstrap/module.mk
include $(SOURCE_DIR)/iso/module.mk
include $(SOURCE_DIR)/upgrade/module.mk
include $(SOURCE_DIR)/virtualbox.mk
