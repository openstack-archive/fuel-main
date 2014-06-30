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

PRODUCT_VERSION:=5.1

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

# Rebuld packages locally (do not use upstream versions)
BUILD_PACKAGES?=1

# Do not compress javascript and css files
NO_UI_OPTIMIZE:=0

# Repos and versions

FUELLIB_COMMIT?=master
NAILGUN_COMMIT?=master
ASTUTE_COMMIT?=master
OSTF_COMMIT?=master

FUELLIB_REPO?=https://github.com/stackforge/fuel-library.git
NAILGUN_REPO?=https://github.com/kozhukalov/fuel-web.git
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

LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/os/$(CENTOS_ARCH)
LOCAL_MIRROR_UBUNTU:=$(LOCAL_MIRROR)/ubuntu
LOCAL_MIRROR_UBUNTU_OS_BASEURL:=$(LOCAL_MIRROR_UBUNTU)
LOCAL_MIRROR_DOCKER:=$(LOCAL_MIRROR)/docker
LOCAL_MIRROR_DOCKER_BASEURL:=$(LOCAL_MIRROR_DOCKER)


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
MIRROR_DOCKER?=$(MIRROR_BASE)/docker
endif
ifeq ($(USE_MIRROR),srt)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://fuel-mirror.srt.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_DOCKER?=$(MIRROR_BASE)/docker
endif
ifeq ($(USE_MIRROR),msk)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://fuel-mirror.msk.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_DOCKER?=$(MIRROR_BASE)/docker
endif
ifeq ($(USE_MIRROR),hrk)
YUM_REPOS?=proprietary
MIRROR_BASE?=http://fuel-mirror.kha.mirantis.net/fwm/$(PRODUCT_VERSION)
MIRROR_CENTOS?=$(MIRROR_BASE)/centos
MIRROR_UBUNTU?=$(MIRROR_BASE)/ubuntu
MIRROR_DOCKER?=$(MIRROR_BASE)/docker
endif

MIRROR_CENTOS?=http://mirrors-local-msk.msk.mirantis.net/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_OS_BASEURL:=$(MIRROR_CENTOS)/os/$(CENTOS_ARCH)
MIRROR_UBUNTU?=http://mirrors-local-msk.msk.mirantis.net/ubuntu/
MIRROR_UBUNTU_OS_BASEURL:=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://fuel-repository.mirantis.com/fwm/$(PRODUCT_VERSION)/docker
MIRROR_DOCKER_BASEURL:=$(MIRROR_DOCKER)
# MIRROR_FUEL option is valid only for 'fuel' YUM_REPOS section
# and ignored in other cases
MIRROR_FUEL?=http://osci-obs.vm.mirantis.net:82/centos-fuel-$(PRODUCT_VERSION)-stable/centos/
MIRROR_FUEL_UBUNTU?=http://osci-obs.vm.mirantis.net:82/ubuntu-fuel-$(PRODUCT_VERSION)-stable/reprepro

REQUIRED_RPMS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-rpm.txt)
REQUIRED_DEBS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-deb.txt)

# Which repositories to use for making local centos mirror.
# Possible values you can find out from mirror/centos/yum_repos.mk file.
# The actual name will be constracted wich prepending "yum_repo_" prefix.
# Example: YUM_REPOS?=official epel => yum_repo_official and yum_repo_epel
# will be used.
YUM_REPOS?=official fuel subscr_manager

# Additional CentOS repos.
# Each repo must be comma separated tuple with repo-name and repo-path.
# Repos must be separated by space.
# Example: EXTRA_RPM_REPOS=lolo,http://my.cool.repo/rpm bar,ftp://repo.foo
EXTRA_RPM_REPOS?=http://mirrors.msk.mirantis.net/centos/$(CENTOS_RELEASE)

# Additional Ubunutu repos.
# Each repo must consist of an url, dist and section parts.
# Repos must be separated by bar.
# Example:
# EXTRA_DEB_REPOS=http://mrr.lcl raring main|http://mirror.yandex.ru/ubuntu precise main
# EXTRA_DEB_REPOS?=http://mirror.yandex.ru/ubuntu/ precise main universe multiverse restricted
EXTRA_DEB_REPOS=http://osci-obs.vm.mirantis.net:82/ubuntu-fuel-5.1-stable-16498/ubuntu /

# Comma or space separated list. Available feature groups:
#   experimental - allow experimental options
#   mirantis - enable Mirantis logos and support page
FEATURE_GROUPS?=experimental
comma:=,
FEATURE_GROUPS:=$(subst $(comma), ,$(FEATURE_GROUPS))

# INTEGRATION TEST CONFIG
NOFORWARD:=1

# Path to yaml configuration file to build ISO ks.cfg
KSYAML?=$(SOURCE_DIR)/iso/ks.yaml

# Docker prebuilt containers. Default is to build containers during ISO build
DOCKER_PREBUILT?=0

# Source of docker prebuilt containers archive. Works only if DOCKER_PREBUILT=true
# Examples:
# DOCKER_PREBUILT_SOURCE=http://srv11-msk.msk.mirantis.net/docker-test/fuel-images.tar.lrz
# DOCKER_PREBUILT_SOURCE=/var/fuel-images.tar.lrz make docker
DOCKER_PREBUILT_SOURCE?=http://srv11-msk.msk.mirantis.net/docker-test/fuel-images.tar.lrz

# Production variable (prod, dev, docker)
PRODUCTION?=docker
