ifndef LOCAL_MIRROR
LOCAL_MIRROR:=$(BUILD_DIR)/local_mirror
endif


# iso.path:=$(BUILD_DIR)/iso/nailgun-centos-6.3-amd64.iso

# bootstrap.linux:=$(BUILD_DIR)/bootstrap/linux
# bootstrap.initrd:=$(BUILD_DIR)/bootstrap/initrd.gz

# # CENTOS REPOSITORIES SETTINGS

# CENTOS_MAJOR:=6
# CENTOS_MINOR:=3
# CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
# CENTOS_ARCH:=x86_64
# CENTOS_MIRROR:=http://mirror.yandex.ru/centos/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)
# CENTOS_NETINSTALL:=http://mirror.yandex.ru/centos/$(CENTOS_RELEASE)/isos/$(CENTOS_ARCH)
# CENTOS_GPG:=http://mirror.yandex.ru/centos

# CENTOS_REPO_DIR:=$(LOCAL_MIRROR)/centos/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)/
# CENTOS_ISO_DIR:=$(LOCAL_MIRROR)/centos/$(CENTOS_RELEASE)/isos/$(CENTOS_ARCH)/


BOOTSTRAP_FILES:=initramfs.img linux
NETINSTALL_ISO:=CentOS-$(CENTOS_RELEASE)-$(CENTOS_ARCH)-minimal-EFI.iso


