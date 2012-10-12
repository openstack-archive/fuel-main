
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

CENTOS_63_ISO:=$(BINARIES_DIR)/CentOS-6.3-x86_64-minimal.iso
CENTOS_63_ROOT:=$(BUILD_DIR)/images/centos-6.3-minimal
CENTOS_63_MAJOR:=6
CENTOS_63_RELEASE:=6.3
CENTOS_63_ARCH:=x86_64
$(call image-mount-rules,CENTOS_63)
