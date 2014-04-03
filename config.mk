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

PRODUCT_VERSION:=5.0

CENTOS_MAJOR:=6
CENTOS_MINOR:=5
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
FUELLIB_COMMIT?=master
NAILGUN_COMMIT?=master
ASTUTE_COMMIT?=master
OSTF_COMMIT?=master

FUELLIB_REPO?=https://github.com/stackforge/fuel-library.git
NAILGUN_REPO?=https://github.com/stackforge/fuel-web.git
ASTUTE_REPO?=https://github.com/stackforge/fuel-astute.git
OSTF_REPO?=https://github.com/stackforge/fuel-ostf.git

# Gerrit URLs and commits
FUELLIB_GERRIT_URL?=https://review.openstack.org/stackforge/fuel-library
NAILGUN_GERRIT_URL?=https://review.openstack.org/stackforge/fuel-web
ASTUTE_GERRIT_URL?=https://review.openstack.org/stackforge/fuel-astute
OSTF_GERRIT_URL?=https://review.openstack.org/stackforge/fuel-ostf

FUELLIB_GERRIT_COMMIT?=none
NAILGUN_GERRIT_COMMIT?=none
ASTUTE_GERRIT_COMMIT?=none
OSTF_GERRIT_COMMIT?=none

LOCAL_MIRROR_SRC:=$(LOCAL_MIRROR)/src
LOCAL_MIRROR_EGGS:=$(LOCAL_MIRROR)/eggs
LOCAL_MIRROR_GEMS:=$(LOCAL_MIRROR)/gems
LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/os/$(CENTOS_ARCH)
LOCAL_MIRROR_UBUNTU:=$(LOCAL_MIRROR)/ubuntu
LOCAL_MIRROR_UBUNTU_OS_BASEURL:=$(LOCAL_MIRROR_UBUNTU)
LOCAL_MIRROR_RHEL:=$(LOCAL_MIRROR)/rhel
LOCAL_MIRROR_DOCKER:=$(LOCAL_MIRROR)/docker

BUILD_MIRROR_GEMS:=$(BUILD_DIR)/packages/gems

# Use download.mirantis.com mirror by default. Other possible values are
# 'msk', 'srt', 'usa', 'hrk'.
# Setting any other value or removing of this variable will cause
# download of all the packages directly from internet
USE_MIRROR?=ext
ifeq ($(USE_MIRROR),ext)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://fuel-repository.mirantis.com/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),srt)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://fuel-mirror.srt.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),msk)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://fuel-mirror.msk.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),usa)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://ss0078.svwh.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif
ifeq ($(USE_MIRROR),hrk)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://fuel-mirror.kha.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_EGGS?=$(MIRROR_BASE)/eggs
MIRROR_GEMS?=$(MIRROR_BASE)/gems
MIRROR_SRC?=$(MIRROR_BASE)/src
endif

MIRROR_CENTOS?=http://mirrors.msk.mirantis.net/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_OS_BASEURL:=$(MIRROR_CENTOS)/os/$(CENTOS_ARCH)
MIRROR_UBUNTU?=http://mirrors.msk.mirantis.net/ubuntu/
MIRROR_UBUNTU_OS_BASEURL:=$(MIRROR_UBUNTU)
MIRROR_RHEL?=http://srv11-msk.msk.mirantis.net/rhel6/rhel-6-server-rpms
MIRROR_RHEL_BOOT?=http://srv11-msk.msk.mirantis.net/rhel6/rhel-server-6.4-x86_64
MIRROR_CENTOS_OS_BASEURL:=$(MIRROR_CENTOS)/docker/
# MIRROR_FUEL option is valid only for 'fuel' YUM_REPOS section
# and ignored in other cases
MIRROR_FUEL?=http://osci-obs.vm.mirantis.net:82/centos-fuel-$(PRODUCT_VERSION)-stable/centos/
MIRROR_FUEL_UBUNTU?=http://osci-obs.vm.mirantis.net:82/ubuntu-fuel-$(PRODUCT_VERSION)-stable/reprepro
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

# Additional CentOS repos.
# Each repo must be comma separated tuple with repo-name and repo-path.
# Repos must be separated by space.
# Example: EXTRA_RPM_REPOS="lolo,http://my.cool.repo/rpm bar,ftp://repo.foo"
EXTRA_RPM_REPOS?=

# Additional Ubunutu repos.
# Each repo must consist of an url, dist and section parts.
# Repos must be separated by bar.
# Example:
# EXTRA_DEB_REPOS="http://mrr.lcl raring main|http://mirror.yandex.ru/ubuntu precise main"'
EXTRA_DEB_REPOS?=

# Mirror of source packages. Bareword 'internet' is used to download packages
# directly from the internet
MIRROR_SRC?=internet

MIRANTIS?=no

# INTEGRATION TEST CONFIG
NOFORWARD:=1

# Path to yaml configuration file to build ISO ks.cfg
KSYAML?=$(SOURCE_DIR)/iso/ks.yaml

# Production variable (prod, dev)
PRODUCTION?=dev

