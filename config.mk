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
PRODUCT_VERSION:=1.0-rc1

CENTOS_MAJOR:=6
CENTOS_MINOR:=3
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
CENTOS_ARCH:=x86_64

ISO_NAME?=fuelweb-centos-$(CENTOS_RELEASE)-$(CENTOS_ARCH)
ISO_DIR?=$(BUILD_DIR)/iso
ISO_DIR:=$(abspath $(ISO_DIR))
ISO_PATH:=$(ISO_DIR)/$(ISO_NAME).iso
IMG_PATH:=$(ISO_DIR)/$(ISO_NAME).img

# Do not compress javascript and css files
NO_UI_OPTIMIZE:=0

LOCAL_MIRROR_SRC:=$(LOCAL_MIRROR)/src
LOCAL_MIRROR_EGGS:=$(LOCAL_MIRROR)/eggs
LOCAL_MIRROR_GEMS:=$(LOCAL_MIRROR)/gems
LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)

BUILD_MIRROR_GEMS:=$(BUILD_DIR)/packages/gems

# Use srv08 mirrors by default. Other possible default is 'msk'.
# Setting any other value or removing of this variable will cause
# download of all the packages directly from internet
USE_MIRROR?=srv08
ifeq ($(USE_MIRROR),srv08)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://srv08-srt.srt.mirantis.net/fwm
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),msk)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://172.18.8.209/fwm
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),msk2)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://172.18.8.207/fwm
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif

MIRROR_CENTOS?=http://archive.kernel.org/centos
MIRROR_CENTOS_OS_BASEURL:=$(MIRROR_CENTOS)/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)
# It can be any a list of links (--find-links) or a pip index (--index-url).
MIRROR_EGGS?=http://pypi.python.org/simple
# NOTE(mihgen): removed gemcutter - it redirects to rubygems.org and has issues w/certificate now
MIRROR_GEMS?=http://rubygems.org

REQUIRED_RPMS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-rpm.txt)
REQUIRED_EGGS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-eggs.txt)
REQUIRED_SRCS:=$(shell grep -v ^\\s*\# $(SOURCE_DIR)/requirements-src.txt)

# Which repositories to use for making local centos mirror.
# Possible values you can find out from mirror/centos/yum_repos.mk file.
# The actual name will be constracted wich prepending "yum_repo_" prefix.
# Example: YUM_REPOS?=official epel => yum_repo_official and yum_repo_epel
# will be used.
YUM_REPOS?=official fuel_folsom_2_1 puppetlabs

# Mirror of source packages. Bareword 'internet' is used to download packages
# directly from the internet
MIRROR_SRC?=internet

# INTEGRATION TEST CONFIG
NOFORWARD:=1
