
/:=$(BUILD_DIR)/bootstrap/

.PHONY: bootstrap
all: bootstrap

.PHONY: clean
clean: $/umount_orig $/umount_initrd-loop $/rm_bootstrap

$/umount_orig:
	-sudo umount $/orig

$/umount_initrd-loop:
	-sudo umount $/initrd-loop

$/rm_bootstrap:
	sudo rm -rf $/


ifndef BINARIES_DIR
$/%:
	$(error BINARIES_DIR variable is not defined)
else

ISO_IMAGE:=$(BINARIES_DIR)/ubuntu-12.04-server-amd64.iso

%: /:=$/

bootstrap: $/linux $/initrd.gz

# it is needed in order to create BUILD_DIR with owner different from root
$/bootstrap.prepare:
	mkdir -p $/

$/bootstrap.build:
	sudo BINARIES_DIR=$(BINARIES_DIR) BASEDIR=$/ bootstrap/bootstrapbuild.sh 

.PHONY: $/bootstrap.prepare $/bootstrap.build

$/linux $/initrd.gz: $/bootstrap.prepare $/bootstrap.build

endif