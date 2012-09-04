
define image-mount-rules-template
$($1_ROOT)/%: $1_ISO:=$($1_ISO)
$($1_ROOT)/%: $1_ROOT:=$($1_ROOT)

$($1_ROOT)/%:
	mkdir -p $$(@D)
	fuseiso $$($1_ISO) $$($1_ROOT)

clean: $($1_ROOT)/umount

.PHONY: $($1_ROOT)/mount $($1_ROOT)/umount
$($1_ROOT)/mount:

$($1_ROOT)/umount:
	-fusermount -u $$($1_ROOT)

endef

image-mount-rules=$(eval $(call image-mount-rules-template,$1,$2,$3))


UBUNTU_1204_ISO:=$(BINARIES_DIR)/ubuntu-12.04-server-amd64.iso
UBUNTU_1204_ROOT:=$(BUILD_DIR)/images/ubuntu-12.04-server
UBUNTU_1204_RELEASE:=precise
UBUNTU_1204_VERSION:=12.04
$(call image-mount-rules,UBUNTU_1204)

$(UBUNTU_1204_ROOT): $(UBUNTU_1204_ROOT)/md5sum.txt

CENTOS_63_MAJOR:=6
CENTOS_63_RELEASE:=6.3
CENTOS_63_ARCH:=x86_64
