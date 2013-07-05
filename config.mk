#
# Build directives. Can be overrided by environment variables.
#

# Base path for build and mirror directories.
# Default value: current directory
TOP_DIR?=$(PWD)
TOP_DIR:=$(abspath $(TOP_DIR))
# Path for build artifacts
BUILD_DIR?=$(TOP_DIR)/build
BUILD_DIR:=$(abspath $(BUILD_DIR))
# Path for cache of downloaded packages
LOCAL_MIRROR?=$(TOP_DIR)/local_mirror
LOCAL_MIRROR:=$(abspath $(LOCAL_MIRROR))

COMMIT_SHA:=$(shell git rev-parse --verify HEAD)
PRODUCT_VERSION:=3.1
FUEL_COMMIT_SHA:=$(shell cd fuel && git rev-parse --verify HEAD)

CENTOS_MAJOR:=6
CENTOS_MINOR:=4
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
CENTOS_ARCH:=x86_64

ISO_NAME?=fuelweb-centos-$(CENTOS_RELEASE)-$(CENTOS_ARCH)
ISO_DIR?=$(BUILD_DIR)/iso
ISO_DIR:=$(abspath $(ISO_DIR))
ISO_PATH:=$(ISO_DIR)/$(ISO_NAME).iso
IMG_PATH:=$(ISO_DIR)/$(ISO_NAME).img

# Do not compress javascript and css files
NO_UI_OPTIMIZE:=0

# Do not copy RHEL repo to the iso
CACHE_RHEL:=0

LOCAL_MIRROR_SRC:=$(LOCAL_MIRROR)/src
LOCAL_MIRROR_EGGS:=$(LOCAL_MIRROR)/eggs
LOCAL_MIRROR_GEMS:=$(LOCAL_MIRROR)/gems
LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/os/$(CENTOS_ARCH)
LOCAL_MIRROR_RHEL:=$(LOCAL_MIRROR)/rhel

BUILD_MIRROR_GEMS:=$(BUILD_DIR)/packages/gems

# Use srv08 mirrors by default. Other possible default is 'msk'.
# Setting any other value or removing of this variable will cause
# download of all the packages directly from internet
USE_MIRROR?=srt
ifeq ($(USE_MIRROR),srt)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://srv08-srt.srt.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),msk)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://srv11-msk.msk.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),usa)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://product-vm.vm.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif

MIRROR_CENTOS?=http://mirror.yandex.ru/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_OS_BASEURL:=$(MIRROR_CENTOS)/os/$(CENTOS_ARCH)
MIRROR_RHEL?=http://srv11-msk.msk.mirantis.net/rhel6/rhel-6-server-rpms
MIRROR_RHEL_BOOT?=http://srv11-msk.msk.mirantis.net/rhel6/rhel-server-6.4-x86_64
# It can be any a list of links (--find-links) or a pip index (--index-url).
MIRROR_EGGS?=http://pypi.python.org/simple
# NOTE(mihgen): removed gemcutter - it redirects to rubygems.org and has issues w/certificate now
MIRROR_GEMS?=http://rubygems.org

REQUIRED_RPMS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-rpm.txt)
REQUIRED_EGGS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-eggs.txt)
REQUIRED_SRCS:=$(shell grep -v ^\\s*\# $(SOURCE_DIR)/requirements-src.txt)
REQ_RHEL_RPMS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/puppet/rpmcache/files/required-rpms.txt)
REQ_FUEL_RHEL_RPMS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/puppet/rpmcache/files/req-fuel-rhel.txt)

# Which repositories to use for making local centos mirror.
# Possible values you can find out from mirror/centos/yum_repos.mk file.
# The actual name will be constracted wich prepending "yum_repo_" prefix.
# Example: YUM_REPOS?=official epel => yum_repo_official and yum_repo_epel
# will be used.
YUM_REPOS?=official fuel subscr_manager
ifeq ($(CACHE_RHEL),1)
YUM_REPOS:=$(YUM_REPOS) rhel
endif

# Mirror of source packages. Bareword 'internet' is used to download packages
# directly from the internet
MIRROR_SRC?=internet

# INTEGRATION TEST CONFIG
NOFORWARD:=1

# Path to yaml configuration file to build ISO ks.cfg
KSYAML?=$(SOURCE_DIR)/iso/ks.yaml

