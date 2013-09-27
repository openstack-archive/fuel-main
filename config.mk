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

MASTER_IP?=10.20.0.2
MASTER_DNS?=10.20.0.1
MASTER_NETMASK?=255.255.255.0
MASTER_GW?=10.20.0.1

PRODUCT_VERSION:=3.2

CENTOS_MAJOR:=6
CENTOS_MINOR:=4
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
CENTOS_ARCH:=x86_64
UBUNTU_RELEASE:=precise

ISO_NAME?=fuelweb-centos-$(CENTOS_RELEASE)-$(CENTOS_ARCH)
ISO_DIR?=$(BUILD_DIR)/iso
ISO_DIR:=$(abspath $(ISO_DIR))
ISO_PATH:=$(ISO_DIR)/$(ISO_NAME).iso
IMG_PATH:=$(ISO_DIR)/$(ISO_NAME).img

# Do not compress javascript and css files
NO_UI_OPTIMIZE:=0

# Do not copy RHEL repo to the iso
CACHE_RHEL:=0

# Repos and versions
NAILGUN_COMMIT?=origin/master
ASTUTE_COMMIT?=origin/master
FUELLIB_COMMIT?=origin/master
FUEL_OSTF_COMMIT?=origin/master

NAILGUN_REPO?=https://github.com/Mirantis/fuelweb.git
ASTUTE_REPO?=https://github.com/Mirantis/astute.git
FUELLIB_REPO?=https://github.com/Mirantis/fuel.git
FUEL_OSTF_REPO?=https://github.com/Mirantis/fuel-ostf-tests.git

LOCAL_MIRROR_SRC:=$(LOCAL_MIRROR)/src
LOCAL_MIRROR_EGGS:=$(LOCAL_MIRROR)/eggs
LOCAL_MIRROR_GEMS:=$(LOCAL_MIRROR)/gems
LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/os/$(CENTOS_ARCH)
LOCAL_MIRROR_UBUNTU:=$(LOCAL_MIRROR)/ubuntu
LOCAL_MIRROR_UBUNTU_OS_BASEURL:=$(LOCAL_MIRROR_UBUNTU)/main
LOCAL_MIRROR_RHEL:=$(LOCAL_MIRROR)/rhel

BUILD_MIRROR_GEMS:=$(BUILD_DIR)/packages/gems

# Use download.mirantis.com mirror by default. Other possible values are
# 'msk', 'srt', 'usa'.
# Setting any other value or removing of this variable will cause
# download of all the packages directly from internet
USE_MIRROR?=ext
ifeq ($(USE_MIRROR),ext)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://download.mirantis.com/fuelweb-repo/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),srt)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://srv08-srt.srt.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),msk)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://srv11-msk.msk.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),usa)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://product-vm.vm.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif

#
# OSCI team requirement: build an iso with our srv08 mirror,
# but use their repo for fuel packages. This section is quick
# way to implement it.
# Limitation of the solution: osci repo will be mixed with srv08 mirror.
# If package is missed in osci repo - it will be taken from srv08.
# If package have the same version in osci and in srv08 repos - any copy
# of it will be taken randomly.
#
ifeq ($(USE_MIRROR),osci)
YUM_REPOS?=proprietary fuel
MIRROR_FUEL?=http://download.mirantis.com/epel-fuel-grizzly-3.2/
MIRROR_FUEL_UBUNTU?=http://download.mirantis.com/epel-fuel-grizzly-3.2/
MIRROR_BASE?=http://srv08-srt.srt.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif

MIRROR_CENTOS?=http://mirror.yandex.ru/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_OS_BASEURL:=$(MIRROR_CENTOS)/os/$(CENTOS_ARCH)
MIRROR_UBUNTU?=http://mirror.yandex.ru/ubuntu/dists/$(UBUNTU_RELEASE)
MIRROR_UBUNTU_OS_BASEURL:=$(MIRROR_UBUNTU)/main
MIRROR_RHEL?=http://srv11-msk.msk.mirantis.net/rhel6/rhel-6-server-rpms
MIRROR_RHEL_BOOT?=http://srv11-msk.msk.mirantis.net/rhel6/rhel-server-6.4-x86_64
# MIRROR_FUEL option is valid only for 'fuel' YUM_REPOS section
# and ignored in other cases
MIRROR_FUEL?=http://172.18.165.40:82/centos-fuel-3.2-testing/centos/
MIRROR_FUEL_UBUNTU?=http://172.18.165.40:82/ubuntu-fuel-3.2-testing/reprepro/
# It can be any a list of links (--find-links) or a pip index (--index-url).
MIRROR_EGGS?=http://pypi.python.org/simple
# NOTE(mihgen): removed gemcutter - it redirects to rubygems.org and has issues w/certificate now
MIRROR_GEMS?=http://rubygems.org

# FYI: For rhel cache we parse fuel/deployment/puppet/rpmcache/files/required-rpms.txt
REQUIRED_RPMS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-rpm.txt)
REQUIRED_DEBS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-deb.txt)
# FYI: Also we get eggs for ostf from fuel/deployment/puppet/nailgun/files/venv-ostf.txt file
REQUIRED_EGGS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-eggs.txt)
REQUIRED_SRCS:=$(shell grep -v ^\\s*\# $(SOURCE_DIR)/requirements-src.txt)

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

