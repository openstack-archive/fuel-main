#
# Build directives. Can be overrided by environment variables.
#

# Base path for build and mirror directories.
# Default value: current directory
TOP_DIR?=$(PWD)
TOP_DIR:=$(abspath $(TOP_DIR))
# Working build directory
BUILD_DIR?=$(TOP_DIR)/build
BUILD_DIR:=$(abspath $(BUILD_DIR))
# Path for build artifacts
ARTS_DIR?=$(BUILD_DIR)/artifacts
ARTS_DIR:=$(abspath $(ARTS_DIR))
# Path for cache of downloaded packages
LOCAL_MIRROR?=$(TOP_DIR)/local_mirror
LOCAL_MIRROR:=$(abspath $(LOCAL_MIRROR))

PRODUCT_VERSION?=11.0

# This variable is used for naming of auxillary objects
# related to product: repositories, mirrors etc
PRODUCT_NAME:=mos

CURRENT_VERSION:=$(PRODUCT_VERSION)

PACKAGE_VERSION?=10.0.0
FUEL_LIBRARY_VERSION?=10.0

# Artifacts names
ISO_NAME?=fuel-$(PRODUCT_VERSION)

# Where we put artifacts
ISO_PATH:=$(ARTS_DIR)/$(ISO_NAME).iso

MASTER_IP?=10.20.0.2
MASTER_DNS?=10.20.0.1
MASTER_NETMASK?=255.255.255.0
MASTER_GW?=10.20.0.1

CENTOS_MAJOR?=7
CENTOS_RELEASE:=$(CENTOS_MAJOR)
CENTOS_ARCH:=x86_64

UBUNTU_RELEASE?=xenial
UBUNTU_MAJOR?=16
UBUNTU_MINOR?=04
UBUNTU_RELEASE_NUMBER:=$(UBUNTU_MAJOR).$(UBUNTU_MINOR)
UBUNTU_KERNEL_FLAVOR?=lts-xenial
UBUNTU_NETBOOT_FLAVOR?=netboot
UBUNTU_ARCH:=amd64
UBUNTU_IMAGE_RELEASE:=$(UBUNTU_MAJOR)$(UBUNTU_MINOR)
SEPARATE_IMAGES?=/boot,ext2 /,ext4

# Rebuld packages locally (do not use upstream versions)
BUILD_PACKAGES?=1

# by default we are not allowed to downgrade rpm packages,
# setting this flag to 0 will cause to use repo priorities only (!)
DENY_RPM_DOWNGRADE?=1

# Do not compress javascript and css files
NO_UI_OPTIMIZE:=0

# Repos and versions
FUELLIB_COMMIT?=stable/ocata
NAILGUN_COMMIT?=stable/ocata
PYTHON_FUELCLIENT_COMMIT?=stable/ocata
FUEL_AGENT_COMMIT?=stable/ocata
FUEL_NAILGUN_AGENT_COMMIT?=stable/ocata
ASTUTE_COMMIT?=stable/ocata
OSTF_COMMIT?=stable/ocata
FUEL_MIRROR_COMMIT?=stable/ocata
FUELMENU_COMMIT?=stable/ocata
SHOTGUN_COMMIT?=stable/ocata
NETWORKCHECKER_COMMIT?=stable/ocata
FUELUPGRADE_COMMIT?=stable/ocata
FUEL_UI_COMMIT?=stable/ocata

FUELLIB_REPO?=https://github.com/openstack/fuel-library.git
NAILGUN_REPO?=https://github.com/openstack/fuel-web.git
PYTHON_FUELCLIENT_REPO?=https://github.com/openstack/python-fuelclient.git
FUEL_AGENT_REPO?=https://github.com/openstack/fuel-agent.git
FUEL_NAILGUN_AGENT_REPO?=https://github.com/openstack/fuel-nailgun-agent.git
ASTUTE_REPO?=https://github.com/openstack/fuel-astute.git
OSTF_REPO?=https://github.com/openstack/fuel-ostf.git
FUELMENU_REPO?=https://github.com/openstack/fuel-menu.git
SHOTGUN_REPO?=https://github.com/openstack/shotgun.git
NETWORKCHECKER_REPO?=https://github.com/openstack/network-checker.git
FUEL_UI_REPO?=https://github.com/openstack/fuel-ui.git

# Gerrit URLs and commits
FUELLIB_GERRIT_URL?=https://review.openstack.org/openstack/fuel-library
NAILGUN_GERRIT_URL?=https://review.openstack.org/openstack/fuel-web
PYTHON_FUELCLIENT_GERRIT_URL?=https://review.openstack.org/openstack/python-fuelclient
FUEL_AGENT_GERRIT_URL?=https://review.openstack.org/openstack/fuel-agent
FUEL_NAILGUN_AGENT_GERRIT_URL?=https://review.openstack.org/openstack/fuel-nailgun-agent
ASTUTE_GERRIT_URL?=https://review.openstack.org/openstack/fuel-astute
OSTF_GERRIT_URL?=https://review.openstack.org/openstack/fuel-ostf
FUELMENU_GERRIT_URL?=https://review.openstack.org/openstack/fuel-menu
SHOTGUN_GERRIT_URL?=https://review.openstack.org/openstack/shotgun
NETWORKCHECKER_GERRIT_URL?=https://review.openstack.org/openstack/network-checker
FUEL_UI_GERRIT_URL?=https://review.openstack.org/openstack/fuel-ui

FUELLIB_GERRIT_COMMIT?=none
NAILGUN_GERRIT_COMMIT?=none
PYTHON_FUELCLIENT_GERRIT_COMMIT?=none
FUEL_AGENT_GERRIT_COMMIT?=none
FUEL_NAILGUN_AGENT_GERRIT_COMMIT?=none
ASTUTE_GERRIT_COMMIT?=none
OSTF_GERRIT_COMMIT?=none
FUELMAIN_GERRIT_COMMIT?=none
FUELMENU_GERRIT_COMMIT?=none
SHOTGUN_GERRIT_COMMIT?=none
NETWORKCHECKER_GERRIT_COMMIT?=none
FUEL_UI_GERRIT_COMMIT?=none

LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/os/$(CENTOS_ARCH)
LOCAL_MIRROR_MOS_CENTOS:=$(LOCAL_MIRROR)/mos-centos
LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_MOS_CENTOS)
LOCAL_MIRROR_UBUNTU:=$(LOCAL_MIRROR)/ubuntu
LOCAL_MIRROR_UBUNTU_OS_BASEURL:=$(LOCAL_MIRROR_UBUNTU)

# Use mirror.fuel-infra.org mirror by default. Other possible values are
# 'usa', 'cz'
ifeq ($(USE_MIRROR),usa)
MIRROR_FUEL?=http://mirror.seed-us1.fuel-infra.org/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)/os/x86_64/
MIRROR_UBUNTU?=mirror.seed-us1.fuel-infra.org
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
endif

ifeq ($(USE_MIRROR),cz)
MIRROR_FUEL?=http://mirror.seed-cz1.fuel-infra.org/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)/os/x86_64/
MIRROR_UBUNTU?=mirror.seed-cz1.fuel-infra.org
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
endif

# Which repositories to use for making local centos mirror.
# Possible values you can find out from mirror/centos/yum_repos.mk file.
# The actual name will be constracted prepending "yum_repo_" prefix.
# Example: YUM_REPOS?=official epel => yum_repo_official and yum_repo_epel
# will be used.
YUM_REPOS?=official extras fuel
MIRROR_CENTOS?=http://mirror.centos.org/centos/$(CENTOS_MAJOR)
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
SANDBOX_MIRROR_CENTOS_UPSTREAM?=$(MIRROR_CENTOS)
SANDBOX_MIRROR_EPEL?=http://mirror.yandex.ru/epel
MIRROR_UBUNTU_METHOD?=http
MIRROR_UBUNTU?=mirror.fuel-infra.org
MIRROR_UBUNTU_ROOT?=/pkgs/ubuntu/
MIRROR_UBUNTU_SUITE?=$(UBUNTU_RELEASE)
MIRROR_UBUNTU_SECTION?=main universe multiverse restricted
MIRROR_MOS_UBUNTU_METHOD?=http
MIRROR_MOS_UBUNTU?=mirror.fuel-infra.org
MIRROR_MOS_UBUNTU_ROOT?=/mos-repos/ubuntu/$(PRODUCT_VERSION)
MIRROR_MOS_UBUNTU_SUITE?=$(PRODUCT_NAME)$(PRODUCT_VERSION)
MIRROR_MOS_UBUNTU_SECTION?=main restricted

# MIRROR_FUEL affects build process only if YUM_REPOS variable contains 'fuel'.
# Otherwise it is ignored entirely.
MIRROR_FUEL?=http://mirror.fuel-infra.org/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)/os/x86_64/

# Additional CentOS repos.
# Each repo must be comma separated tuple with repo-name and repo-path.
# Repos must be separated by space.
# Example: EXTRA_RPM_REPOS="lolo,http://my.cool.repo/rpm,priority bar,ftp://repo.foo,priority"
EXTRA_RPM_REPOS?="proposed,http://mirror.fuel-infra.org/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)/snapshots/proposed-latest/x86_64/"

# define RPM repo which contains fuel rpm-build-dep packages, in format
# EXTRA_RPM_BUILDDEP_REPO=http://my.cool.repo/rpm
EXTRA_RPM_BUILDDEP_REPO?="http://mirror.fuel-infra.org/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)/snapshots/proposed-latest/x86_64/"

comma:=,

# Path to yaml configuration file to build ISO ks.cfg
KSYAML?=$(SOURCE_DIR)/iso/ks.yaml

# Copy local /etc/ssl certs inside SANDBOX, which used for build deb mirror and packages.
# This option should be enabled, in case you have to pass https repos for Ubuntu.
SANDBOX_COPY_CERTS?=0

# Development option only:
# Please don’t change them if you don’t know what they do ##

# Work-around for: LP1482667
# If not empty, will try to download prepared upstream puppet modules source,
# which used like requirements for build fuel-library package.
# List of modules, which SHOULD be passed via this file can be found:
# https://github.com/openstack/fuel-library/blob/master/deployment/Puppetfile
#
# Usage example:
# USE_PREDEFINED_FUEL_LIB_PUPPET_MODULES?=http://127.0.0.1/files/upstream_modules.tar.gz
# Content example:
# upstream_modules.tar.gz:\
#  \apt/metadata.json
#  \concat/metadata.json
USE_PREDEFINED_FUEL_LIB_PUPPET_MODULES?=

# proxy configuration in format:
# PROXY_CONFIG="http_proxy=http://proxy_ip_address:proxy_port https_proxy=https://proxy_ip_address:proxy_port no_proxy=localhost"
PROXY_CONFIG?=
