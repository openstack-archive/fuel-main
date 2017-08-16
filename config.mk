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
# Path to pre-built artifacts
DEPS_DIR?=$(TOP_DIR)/deps
DEPS_DIR:=$(abspath $(DEPS_DIR))

PRODUCT_VERSION:=7.0

# This variable is used for naming of auxillary objects
# related to product: repositories, mirrors etc
PRODUCT_NAME:=mos

# This variable is used mostly for
# keeping things uniform. Some files
# contain versions as a part of their paths
# but building process for current version differs from
# ones for other versions which are supposed
# to come from DEPS_DIR "as is"
CURRENT_VERSION:=$(PRODUCT_VERSION)

PACKAGE_VERSION=$(PRODUCT_VERSION).0
UPGRADE_VERSIONS?=$(CURRENT_VERSION)

# Path to pre-built artifacts
DEPS_DIR_CURRENT?=$(DEPS_DIR)/$(CURRENT_VERSION)
DEPS_DIR_CURRENT:=$(abspath $(DEPS_DIR_CURRENT))

# Artifacts names
ISO_NAME?=fuel-$(PRODUCT_VERSION)
UPGRADE_TARBALL_NAME?=fuel-$(PRODUCT_VERSION)-upgrade
OPENSTACK_PATCH_TARBALL_NAME?=fuel-$(PRODUCT_VERSION)-patch
VBOX_SCRIPTS_NAME?=vbox-scripts-$(PRODUCT_VERSION)
BOOTSTRAP_ART_NAME?=bootstrap.tar.gz
DOCKER_ART_NAME?=fuel-images.tar.lrz
VERSION_YAML_ART_NAME?=version.yaml
CENTOS_REPO_ART_NAME?=centos-repo.tar
UBUNTU_REPO_ART_NAME?=ubuntu-repo.tar
PUPPET_ART_NAME?=puppet.tgz
OPENSTACK_YAML_ART_NAME?=openstack.yaml
TARGET_CENTOS_IMG_ART_NAME?=centos_target_images.tar



# Where we put artifacts
ISO_PATH:=$(ARTS_DIR)/$(ISO_NAME).iso
UPGRADE_TARBALL_PATH:=$(ARTS_DIR)/$(UPGRADE_TARBALL_NAME).tar
VBOX_SCRIPTS_PATH:=$(ARTS_DIR)/$(VBOX_SCRIPTS_NAME).zip

MASTER_IP?=10.20.0.2
MASTER_DNS?=10.20.0.1
MASTER_NETMASK?=255.255.255.0
MASTER_GW?=10.20.0.1

CENTOS_MAJOR:=6
CENTOS_MINOR:=9
# For fuel-master
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
CENTOS_ARCH:=x86_64
# Hardcode, don't change those values:
# See LP#1706581 for more info.
#   For bootstrap image:
CENTOS_IMAGE_RELEASE:=66
IBP_CENTOS_RELEASE=6.6
#
UBUNTU_RELEASE:=trusty
UBUNTU_MAJOR:=14
UBUNTU_MINOR:=04
UBUNTU_RELEASE_NUMBER:=$(UBUNTU_MAJOR).$(UBUNTU_MINOR)
UBUNTU_KERNEL_FLAVOR?=lts-trusty
UBUNTU_NETBOOT_FLAVOR?=netboot
UBUNTU_ARCH:=amd64
UBUNTU_IMAGE_RELEASE:=$(UBUNTU_MAJOR)$(UBUNTU_MINOR)
SEPARATE_IMAGES?=/boot,ext2 /,ext4

# Rebuld packages locally (do not use upstream versions):
# BUILD_PACKAGES?=1
BUILD_PACKAGES?=0

# If we are using patching feature, we are not going to build 1-st level
# packages, but we still need to build "packages-late"
PATCHING_CI?=0

# List of packages, which should not be downloaded from upstream centos repos
# Separator=comma
EXLUDE_PACKAGES_CENTOS?=*.i?86,*.i686,,python-requests*,centos-release

# Exclude thus packages, to be installed from naillgun repo
EXLUDE_PACKAGES_CENTOS_NAIGUN?=iwl*-firmware*mira*,libertas-*-firmware*mira*,linux-firmware,kernel*3.10.5*mos*,kernel*2.6.3*mos*,

# by default we are not allowed to downgrade rpm packages,
# setting this flag to 0 will cause to use repo priorities only (!)
DENY_RPM_DOWNGRADE?=1

# Do not compress javascript and css files
NO_UI_OPTIMIZE:=0

# Repos and versions
FUELLIB_COMMIT?=stable/7.0
NAILGUN_COMMIT?=stable/7.0
PYTHON_FUELCLIENT_COMMIT?=stable/7.0
FUEL_AGENT_COMMIT?=stable/7.0
FUEL_NAILGUN_AGENT_COMMIT?=stable/7.0
ASTUTE_COMMIT?=stable/7.0
OSTF_COMMIT?=stable/7.0

FUELLIB_REPO?=https://github.com/openstack/fuel-library.git
NAILGUN_REPO?=https://github.com/openstack/fuel-web.git
PYTHON_FUELCLIENT_REPO?=https://github.com/openstack/python-fuelclient.git
FUEL_AGENT_REPO?=https://github.com/openstack/fuel-agent.git
FUEL_NAILGUN_AGENT_REPO?=https://github.com/openstack/fuel-nailgun-agent.git
ASTUTE_REPO?=https://github.com/openstack/fuel-astute.git
OSTF_REPO?=https://github.com/openstack/fuel-ostf.git

# Gerrit URLs and commits
FUELLIB_GERRIT_URL?=https://review.openstack.org/openstack/fuel-library
NAILGUN_GERRIT_URL?=https://review.openstack.org/openstack/fuel-web
PYTHON_FUELCLIENT_GERRIT_URL?=https://review.openstack.org/openstack/python-fuelclient
FUEL_AGENT_GERRIT_URL?=https://review.openstack.org/openstack/fuel-agent
FUEL_NAILGUN_AGENT_GERRIT_URL?=https://review.openstack.org/openstack/fuel-nailgun-agent
ASTUTE_GERRIT_URL?=https://review.openstack.org/openstack/fuel-astute
OSTF_GERRIT_URL?=https://review.openstack.org/openstack/fuel-ostf

FUELLIB_GERRIT_COMMIT?=none
NAILGUN_GERRIT_COMMIT?=none
PYTHON_FUELCLIENT_GERRIT_COMMIT?=none
FUEL_AGENT_GERRIT_COMMIT?=none
FUEL_NAILGUN_AGENT_GERRIT_COMMIT?=none
ASTUTE_GERRIT_COMMIT?=none
OSTF_GERRIT_COMMIT?=none
FUELMAIN_GERRIT_COMMIT?=none

LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/os/$(CENTOS_ARCH)
LOCAL_MIRROR_UBUNTU:=$(LOCAL_MIRROR)/ubuntu
LOCAL_MIRROR_UBUNTU_OS_BASEURL:=$(LOCAL_MIRROR_UBUNTU)
LOCAL_MIRROR_DOCKER:=$(LOCAL_MIRROR)/docker
LOCAL_MIRROR_DOCKER_BASEURL:=$(LOCAL_MIRROR_DOCKER)

# Use download.mirantis.com mirror by default. Other possible values are
# 'msk', 'srt', 'usa', 'hrk', 'cz'
# Setting any other value or removing of this variable will cause
# download of all the packages directly from internet
USE_MIRROR?=ext

ifeq ($(USE_MIRROR),ext)
MIRROR_CENTOS?=http://mirror.centos.org/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
SANDBOX_MIRROR_CENTOS_UPSTREAM?=http://mirror.karneval.cz/pub/centos/$(CENTOS_RELEASE)
MIRROR_UBUNTU?=mirror.fuel-infra.org
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://mirror.fuel-infra.org/fwm/$(PRODUCT_VERSION)/docker
endif

ifeq ($(USE_MIRROR),srt)
MIRROR_CENTOS?=http://mirror.centos.org/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
MIRROR_UBUNTU?=osci-mirror-srt.srt.mirantis.net
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://osci-mirror-srt.srt.mirantis.net/fwm/$(PRODUCT_VERSION)/docker
endif

ifeq ($(USE_MIRROR),msk)
MIRROR_CENTOS?=http://mirror.centos.org/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
MIRROR_UBUNTU?=osci-mirror-msk.msk.mirantis.net
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://osci-mirror-msk.msk.mirantis.net/fwm/$(PRODUCT_VERSION)/docker
endif

ifeq ($(USE_MIRROR),hrk)
MIRROR_CENTOS?=http://mirror.centos.org/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
MIRROR_UBUNTU?=osci-mirror-kha.kha.mirantis.net
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://osci-mirror-kha.kha.mirantis.net/fwm/$(PRODUCT_VERSION)/docker
endif

ifeq ($(USE_MIRROR),usa)
MIRROR_CENTOS?=http://mirror.centos.org/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
MIRROR_UBUNTU?=mirror.seed-us1.fuel-infra.org
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://mirror.seed-us1.fuel-infra.org/fwm/$(PRODUCT_VERSION)/docker
endif

ifeq ($(USE_MIRROR),cz)
MIRROR_CENTOS?=http://mirror.centos.org/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
MIRROR_UBUNTU?=mirror.seed-cz1.fuel-infra.org
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://mirror.seed-cz1.fuel-infra.org/fwm/$(PRODUCT_VERSION)/docker
endif

# Which repositories to use for making local centos mirror.
# Possible values you can find out from mirror/centos/yum_repos.mk file.
# The actual name will be constracted prepending "yum_repo_" prefix.
# Example: YUM_REPOS?=official epel => yum_repo_official and yum_repo_epel
# will be used.
YUM_REPOS?=official fuel
MIRROR_CENTOS?=http://mirror.centos.org/centos/$(CENTOS_RELEASE)
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
SANDBOX_MIRROR_CENTOS_UPSTREAM?=$(MIRROR_CENTOS)
SANDBOX_MIRROR_EPEL?=http://mirror.yandex.ru/epel/
MIRROR_UBUNTU_METHOD?=http
MIRROR_UBUNTU?=osci-mirror-msk.msk.mirantis.net
MIRROR_UBUNTU_ROOT?=/pkgs/ubuntu/
MIRROR_UBUNTU_SUITE?=$(UBUNTU_RELEASE)
MIRROR_UBUNTU_SECTION?=main universe multiverse restricted
MIRROR_MOS_UBUNTU_METHOD?=http
MIRROR_MOS_UBUNTU?=perestroika-repo-tst.infra.mirantis.net
MIRROR_MOS_UBUNTU_ROOT?=/mos-repos/ubuntu/7.0
MIRROR_MOS_UBUNTU_SUITE?=$(PRODUCT_NAME)$(PRODUCT_VERSION)
MIRROR_MOS_UBUNTU_SECTION?=main restricted
MIRROR_DOCKER?=http://mirror.fuel-infra.org/fwm/$(PRODUCT_VERSION)/docker

# MIRROR_FUEL affects build process only if YUM_REPOS variable contains 'fuel'.
# Otherwise it is ignored entirely.
# MIRROR_FUEL?=http://perestroika-repo-tst.infra.mirantis.net/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos6-fuel/os/x86_64
MIRROR_FUEL?=http://mirror.fuel-infra.org/fwm/$(PRODUCT_VERSION)-release/centos/os/$(CENTOS_ARCH)
#MIRROR_FUEL?=http://perestroika-repo-tst.infra.mirantis.net/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos6-fuel/os/x86_64

# Additional CentOS repos.
# Each repo must be comma separated tuple with repo-name and repo-path.
# Repos must be separated by space.
# Format: EXTRA_RPM_REPOS="anyname,url,priority,exclude_list"
# Default priority=10
# Each item after priority, means to be exluded
# Example: EXTRA_RPM_REPOS="foo,http://my.cool.repo/rpm,priority bar,ftp://repo.foo foo1,http://my.cool.repo/rpm,10,python-requests*,*.i?86,*.i686, foo2,http://my.cool.repo/rpm,,python-requests*,*.i?86,*.i686"
ifndef EXTRA_RPM_REPOS
define EXTRA_RPM_REPOS
fuel-updates,http://mirror.seed-cz1.fuel-infra.org/mos-repos/centos/mos7.0-centos6-fuel/updates/x86_64/,1,$(EXLUDE_PACKAGES_CENTOS_NAIGUN) \
centos-os,$(MIRROR_CENTOS)/os/x86_64/,,$(EXLUDE_PACKAGES_CENTOS) \
centos-updates,$(MIRROR_CENTOS)/updates/x86_64/,,$(EXLUDE_PACKAGES_CENTOS) \
centos-extras,$(MIRROR_CENTOS)/extras/x86_64/,,$(EXLUDE_PACKAGES_CENTOS)
endef
endif

# Comma or space separated list. Available feature groups:
#   experimental - allow experimental options
#   mirantis - enable Mirantis logos and support page
FEATURE_GROUPS?=experimental
comma:=,
FEATURE_GROUPS:=$(subst $(comma), ,$(FEATURE_GROUPS))

# Path to yaml configuration file to build ISO ks.cfg
KSYAML?=$(SOURCE_DIR)/iso/ks.yaml

# Production variable (prod, dev, docker)
PRODUCTION?=docker

# Copy local /etc/ssl certs inside SANDBOX, which used for build deb mirror and packages.
# This option should be enabled, in case you have to pass https repos for Ubuntu.
SANDBOX_COPY_CERTS?=0

# Development option only:
# Please don't change them if you don't know what they do ##

# If not empty, will try save "build/upgrade/deps" pip cache from upgrade module only,
# to file  $(ARTS_DIR)/$(SAVE_UPGRADE_PIP_ART)
# Example:
# SAVE_UPGRADE_PIP_ART?=fuel-dev.art_pip_from_upg_module.tar.gz
SAVE_UPGRADE_PIP_ART?=

# If not empty, will try to download this archive and use like pip cache
# for creating upgrade module.
# Example:
# USE_UPGRADE_PIP_ART_HTTP_LINK?=http://127.0.0.1/files/deps.pip.tar.gz
# Content example:
# deps.pip.tar.gz:\
#  \argparse-1.2.1.tar.gz
#  \docker-py-0.3.2.tar.gz
USE_UPGRADE_PIP_ART_HTTP_LINK?=

# Work-around for: LP1482667
# If not empty, will try to download prepeared upstream puppet modules source,
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
