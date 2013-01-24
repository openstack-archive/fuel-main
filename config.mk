PWD:=$(shell pwd -P)

SOURCE_DIR:=$(PWD)

ifndef BUILD_DIR
BUILD_DIR:=$(PWD)/build
endif

ifndef LOCAL_MIRROR
LOCAL_MIRROR:=local_mirror
endif

LOCAL_MIRROR_SRC:=$(LOCAL_MIRROR)/src
LOCAL_MIRROR_EGGS:=$(LOCAL_MIRROR)/eggs
LOCAL_MIRROR_GEMS:=$(LOCAL_MIRROR)/gems

CENTOS_MAJOR:=6
CENTOS_MINOR:=3
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
CENTOS_ARCH:=x86_64
LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)


REQUIRED_PACKAGES:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-rpm.txt)
RPMFORGE_PACKAGES:=qemu

REQUIRED_EGGS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-eggs.txt)
SRC_URLS:=$(shell grep -v ^\\s*\# $(SOURCE_DIR)/requirements-src.txt)

# It can be any a list of links (--find-links) or a pip index (--index-url).
MIRROR_EGGS:=http://pypi.python.org/simple


CENTOS_MIRROR:=http://mirror.yandex.ru/centos
CENTOS_MIRROR_OS_BASEURL:=$(CENTOS_MIRROR)/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)

# Which repositories to use for making local centos mirror.
# Possible values you can find out from mirror/centos/yum_repos.mk file.
# The actual name will be constracted wich prepending "yum_repo_" prefix.
# Example: YUM_REPOS:=centos epel => yum_repo_centos and yum_repo_epel
# will be used.
YUM_REPOS:=centos epel fuel_folsom puppetlabs rpmforge

BOOTSTRAP_FILES:=initramfs.img linux
NETINSTALL_ISO:=CentOS-$(CENTOS_RELEASE)-$(CENTOS_ARCH)-minimal-EFI.iso


