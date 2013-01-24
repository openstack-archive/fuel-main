CENTOS_MAJOR:=6
CENTOS_MINOR:=3
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
CENTOS_ARCH:=x86_64

ifeq ($(LOCAL_MIRROR),)
$(error It seems that variable LOCAL_MIRROR was not set correctly)
endif

LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)

REQUIRED_PACKAGES:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-rpm.txt)
RPMFORGE_PACKAGES:=qemu

CENTOS_MIRROR:=http://mirror.yandex.ru/centos
CENTOS_MIRROR_OS_BASEURL:=$(CENTOS_MIRROR)/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)

YUM_REPOS:=centos epel fuel_folsom puppetlabs rpmforge

include $(SOURCE_DIR)/mirror/centos/config_yum.mk