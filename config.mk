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

PRODUCT_VERSION:=9.0

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

# Path to pre-built artifacts
DEPS_DIR_CURRENT?=$(DEPS_DIR)/$(CURRENT_VERSION)
DEPS_DIR_CURRENT:=$(abspath $(DEPS_DIR_CURRENT))

# Artifacts names
ISO_NAME?=fuel-$(PRODUCT_VERSION)
VBOX_SCRIPTS_NAME?=vbox-scripts-$(PRODUCT_VERSION)
BOOTSTRAP_ART_NAME?=bootstrap.tar.gz
DOCKER_ART_NAME?=fuel-images.tar.lrz
VERSION_YAML_ART_NAME?=version.yaml
CENTOS_REPO_ART_NAME?=centos-repo.tar
UBUNTU_REPO_ART_NAME?=ubuntu-repo.tar
PUPPET_ART_NAME?=puppet.tgz


# Where we put artifacts
ISO_PATH:=$(ARTS_DIR)/$(ISO_NAME).iso
VBOX_SCRIPTS_PATH:=$(ARTS_DIR)/$(VBOX_SCRIPTS_NAME).zip

MASTER_IP?=10.20.0.2
MASTER_DNS?=10.20.0.1
MASTER_NETMASK?=255.255.255.0
MASTER_GW?=10.20.0.1

USE_VAULT?=none
CENTOS_MAJOR?=7
CENTOS_MINOR?=1
CENTOS_BUILD?=1503
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR).$(CENTOS_BUILD)
CENTOS_ARCH:=x86_64
CENTOS_IMAGE_RELEASE:=$(CENTOS_MAJOR)$(CENTOS_MINOR)
UBUNTU_RELEASE:=trusty
UBUNTU_MAJOR:=14
UBUNTU_MINOR:=04
UBUNTU_RELEASE_NUMBER:=$(UBUNTU_MAJOR).$(UBUNTU_MINOR)
UBUNTU_KERNEL_FLAVOR?=lts-trusty
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
FUELLIB_COMMIT?=master
NAILGUN_COMMIT?=master
PYTHON_FUELCLIENT_COMMIT?=master
FUEL_AGENT_COMMIT?=master
FUEL_NAILGUN_AGENT_COMMIT?=master
ASTUTE_COMMIT?=master
OSTF_COMMIT?=master
FUEL_MIRROR_COMMIT?=master
FUELMENU_COMMIT?=master
SHOTGUN_COMMIT?=master
NETWORKCHECKER_COMMIT?=master
FUELUPGRADE_COMMIT?=master

FUELLIB_REPO?=https://github.com/openstack/fuel-library.git
NAILGUN_REPO?=https://github.com/openstack/fuel-web.git
PYTHON_FUELCLIENT_REPO?=https://github.com/openstack/python-fuelclient.git
FUEL_AGENT_REPO?=https://github.com/openstack/fuel-agent.git
FUEL_NAILGUN_AGENT_REPO?=https://github.com/openstack/fuel-nailgun-agent.git
ASTUTE_REPO?=https://github.com/openstack/fuel-astute.git
OSTF_REPO?=https://github.com/openstack/fuel-ostf.git
FUEL_MIRROR_REPO?=https://github.com/openstack/fuel-mirror.git
FUELMENU_REPO?=https://github.com/openstack/fuel-menu.git
SHOTGUN_REPO?=https://github.com/openstack/shotgun.git
NETWORKCHECKER_REPO?=https://github.com/openstack/network-checker.git
FUELUPGRADE_REPO?=https://github.com/openstack/fuel-upgrade.git

# Gerrit URLs and commits
FUELLIB_GERRIT_URL?=https://review.openstack.org/openstack/fuel-library
NAILGUN_GERRIT_URL?=https://review.openstack.org/openstack/fuel-web
PYTHON_FUELCLIENT_GERRIT_URL?=https://review.openstack.org/openstack/python-fuelclient
FUEL_AGENT_GERRIT_URL?=https://review.openstack.org/openstack/fuel-agent
FUEL_NAILGUN_AGENT_GERRIT_URL?=https://review.openstack.org/openstack/fuel-nailgun-agent
ASTUTE_GERRIT_URL?=https://review.openstack.org/openstack/fuel-astute
OSTF_GERRIT_URL?=https://review.openstack.org/openstack/fuel-ostf
FUEL_MIRROR_GERRIT_URL?=https://review.openstack.org/openstack/fuel-mirror
FUELMENU_GERRIT_URL?=https://review.openstack.org/openstack/fuel-menu
SHOTGUN_GERRIT_URL?=https://review.openstack.org/openstack/shotgun
NETWORKCHECKER_GERRIT_URL?=https://review.openstack.org/openstack/network-checker
FUELUPGRADE_GERRIT_URL?=https://review.openstack.org/openstack/fuel-upgrade

FUELLIB_GERRIT_COMMIT?=none
NAILGUN_GERRIT_COMMIT?=none
PYTHON_FUELCLIENT_GERRIT_COMMIT?=none
FUEL_AGENT_GERRIT_COMMIT?=none
FUEL_NAILGUN_AGENT_GERRIT_COMMIT?=none
ASTUTE_GERRIT_COMMIT?=none
OSTF_GERRIT_COMMIT?=none
FUEL_MIRROR_GERRIT_COMMIT?=none
FUELMAIN_GERRIT_COMMIT?=none
FUELMENU_GERRIT_COMMIT?=none
SHOTGUN_GERRIT_COMMIT?=none
NETWORKCHECKER_GERRIT_COMMIT?=none
FUELUPGRADE_GERRIT_COMMIT?=none

LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/os/$(CENTOS_ARCH)
LOCAL_MIRROR_MOS_CENTOS:=$(LOCAL_MIRROR)/mos-centos
LOCAL_MIRROR_MOS_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_MOS_CENTOS)
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
MIRROR_FUEL?=http://mirror.fuel-infra.org/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)-fuel/os/x86_64/
ifeq ($(USE_VAULT),none)
MIRROR_CENTOS?=http://mirror.centos.org/centos/$(CENTOS_MAJOR)
else
MIRROR_CENTOS?=http://vault.centos.org/$(CENTOS_RELEASE)
endif
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
SANDBOX_MIRROR_CENTOS_UPSTREAM?=$(MIRROR_CENTOS)
MIRROR_UBUNTU?=mirror.fuel-infra.org
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://mirror.fuel-infra.org/docker/$(PRODUCT_VERSION)
endif

ifeq ($(USE_MIRROR),srt)
MIRROR_FUEL?=http://osci-mirror-srt.srt.mirantis.net/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)-fuel/os/x86_64/
MIRROR_UBUNTU?=osci-mirror-srt.srt.mirantis.net
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://osci-mirror-srt.srt.mirantis.net/docker/$(PRODUCT_VERSION)
endif

ifeq ($(USE_MIRROR),msk)
MIRROR_FUEL?=http://osci-mirror-msk.msk.mirantis.net/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)-fuel/os/x86_64/
MIRROR_UBUNTU?=osci-mirror-msk.msk.mirantis.net
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://osci-mirror-msk.msk.mirantis.net/docker/$(PRODUCT_VERSION)
endif

ifeq ($(USE_MIRROR),hrk)
MIRROR_FUEL?=http://osci-mirror-kha.kha.mirantis.net/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)-fuel/os/x86_64/
MIRROR_UBUNTU?=osci-mirror-kha.kha.mirantis.net
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://osci-mirror-kha.kha.mirantis.net/docker/$(PRODUCT_VERSION)
endif

ifeq ($(USE_MIRROR),usa)
MIRROR_FUEL?=http://mirror.seed-us1.fuel-infra.org/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)-fuel/os/x86_64/
MIRROR_UBUNTU?=mirror.seed-us1.fuel-infra.org
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://mirror.seed-us1.fuel-infra.org/docker/$(PRODUCT_VERSION)
endif

ifeq ($(USE_MIRROR),cz)
MIRROR_FUEL?=http://mirror.seed-cz1.fuel-infra.org/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)-fuel/os/x86_64/
MIRROR_UBUNTU?=mirror.seed-cz1.fuel-infra.org
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://mirror.seed-cz1.fuel-infra.org/docker/$(PRODUCT_VERSION)
endif

# Which repositories to use for making local centos mirror.
# Possible values you can find out from mirror/centos/yum_repos.mk file.
# The actual name will be constracted prepending "yum_repo_" prefix.
# Example: YUM_REPOS?=official epel => yum_repo_official and yum_repo_epel
# will be used.
YUM_REPOS?=official extras fuel
ifeq ($(USE_VAULT),none)
MIRROR_CENTOS?=http://mirror.centos.org/centos/$(CENTOS_MAJOR)
else
MIRROR_CENTOS?=http://vault.centos.org/$(CENTOS_RELEASE)
endif
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
SANDBOX_MIRROR_CENTOS_UPSTREAM?=$(MIRROR_CENTOS)
SANDBOX_MIRROR_EPEL?=http://mirror.yandex.ru/epel
MIRROR_UBUNTU_METHOD?=http
MIRROR_UBUNTU?=osci-mirror-msk.msk.mirantis.net
MIRROR_UBUNTU_ROOT?=/pkgs/ubuntu/
MIRROR_UBUNTU_SUITE?=$(UBUNTU_RELEASE)
MIRROR_UBUNTU_SECTION?=main universe multiverse restricted
MIRROR_MOS_UBUNTU_METHOD?=http
MIRROR_MOS_UBUNTU?=perestroika-repo-tst.infra.mirantis.net
MIRROR_MOS_UBUNTU_ROOT?=/mos-repos/ubuntu/$(PRODUCT_VERSION)
MIRROR_MOS_UBUNTU_SUITE?=$(PRODUCT_NAME)$(PRODUCT_VERSION)
MIRROR_MOS_UBUNTU_SECTION?=main restricted
# NOTE(kozhukalov): We are getting rid of staging mirrors (FWM) which are built using 'make mirror' command.
# But we still need a place where we can download docker base images. They are quite stable
# and we just put them manually under this URL.
MIRROR_DOCKER?=http://mirror.fuel-infra.org/docker/$(PRODUCT_VERSION)

# MIRROR_FUEL affects build process only if YUM_REPOS variable contains 'fuel'.
# Otherwise it is ignored entirely.
MIRROR_FUEL?=http://mirror.fuel-infra.org/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)-fuel/os.target.txt

# Additional CentOS repos.
# Each repo must be comma separated tuple with repo-name and repo-path.
# Repos must be separated by space.
# Example: EXTRA_RPM_REPOS="lolo,http://my.cool.repo/rpm,priority bar,ftp://repo.foo,priority"
EXTRA_RPM_REPOS?=

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
# Please don’t change them if you don’t know what they do ##

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

# If the URL given ended with target.txt then is't a pointer to a snapshot that
# should be unlinked. If it is not - return it as is.
expand_repo_url=$(shell url=$1; echo $${url} | grep -q -e '.*\.target\.txt$$' && echo "$${url%/*}/$$(curl -sSf $$url | head -1)/x86_64/" || echo $${url})

# Expand repo URLs now
#MIRROR_CENTOS:=$(call expand_repo_url,$(MIRROR_CENTOS))
#MIRROR_CENTOS_KERNEL:=$(call expand_repo_url,$(MIRROR_CENTOS_KERNEL))
#SANDBOX_MIRROR_CENTOS_UPSTREAM:=$(call expand_repo_url,$(SANDBOX_MIRROR_CENTOS_UPSTREAM))
MIRROR_FUEL:=$(call expand_repo_url,$(MIRROR_FUEL))
