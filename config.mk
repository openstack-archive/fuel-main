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
CENTOS_MINOR:=5
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
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

FUELLIB_REPO?=https://github.com/stackforge/fuel-library.git
NAILGUN_REPO?=https://github.com/stackforge/fuel-web.git
PYTHON_FUELCLIENT_REPO?=https://github.com/stackforge/python-fuelclient.git
FUEL_AGENT_REPO?=https://github.com/stackforge/fuel-agent.git
FUEL_NAILGUN_AGENT_REPO?=https://github.com/stackforge/fuel-nailgun-agent.git
ASTUTE_REPO?=https://github.com/stackforge/fuel-astute.git
OSTF_REPO?=https://github.com/stackforge/fuel-ostf.git

# Gerrit URLs and commits
FUELLIB_GERRIT_URL?=https://review.openstack.org/stackforge/fuel-library
NAILGUN_GERRIT_URL?=https://review.openstack.org/stackforge/fuel-web
PYTHON_FUELCLIENT_GERRIT_URL?=https://review.openstack.org/stackforge/python-fuelclient
FUEL_AGENT_GERRIT_URL?=https://review.openstack.org/stackforge/fuel-agent
FUEL_NAILGUN_AGENT_GERRIT_URL?=https://review.openstack.org/stackforge/fuel-nailgun-agent
ASTUTE_GERRIT_URL?=https://review.openstack.org/stackforge/fuel-astute
OSTF_GERRIT_URL?=https://review.openstack.org/stackforge/fuel-ostf

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
YUM_REPOS?=proprietary
MIRROR_CENTOS?=http://mirror.fuel-infra.org/fwm/$(PRODUCT_VERSION)/centos
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
SANDBOX_MIRROR_CENTOS_UPSTREAM?=http://vault.centos.org/$(CENTOS_RELEASE)
MIRROR_UBUNTU?=mirror.fuel-infra.org
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://mirror.fuel-infra.org/fwm/$(PRODUCT_VERSION)/docker
endif

ifeq ($(USE_MIRROR),srt)
YUM_REPOS?=proprietary
MIRROR_CENTOS?=http://osci-mirror-srt.srt.mirantis.net/fwm/$(PRODUCT_VERSION)/centos
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
MIRROR_UBUNTU?=osci-mirror-srt.srt.mirantis.net
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://osci-mirror-srt.srt.mirantis.net/fwm/$(PRODUCT_VERSION)/docker
endif

ifeq ($(USE_MIRROR),msk)
YUM_REPOS?=proprietary
MIRROR_CENTOS?=http://osci-mirror-msk.msk.mirantis.net/fwm/$(PRODUCT_VERSION)/centos
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
MIRROR_UBUNTU?=osci-mirror-msk.msk.mirantis.net
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://osci-mirror-msk.msk.mirantis.net/fwm/$(PRODUCT_VERSION)/docker
endif

ifeq ($(USE_MIRROR),hrk)
YUM_REPOS?=proprietary
MIRROR_CENTOS?=http://osci-mirror-kha.kha.mirantis.net/fwm/$(PRODUCT_VERSION)/centos
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
MIRROR_UBUNTU?=osci-mirror-kha.kha.mirantis.net
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://osci-mirror-kha.kha.mirantis.net/fwm/$(PRODUCT_VERSION)/docker
endif

ifeq ($(USE_MIRROR),usa)
YUM_REPOS?=proprietary
MIRROR_CENTOS?=http://mirror.seed-us1.fuel-infra.org/fwm/$(PRODUCT_VERSION)/centos
MIRROR_CENTOS_KERNEL?=$(MIRROR_CENTOS)
MIRROR_UBUNTU?=mirror.seed-us1.fuel-infra.org
MIRROR_MOS_UBUNTU?=$(MIRROR_UBUNTU)
MIRROR_DOCKER?=http://mirror.seed-us1.fuel-infra.org/fwm/$(PRODUCT_VERSION)/docker
endif

ifeq ($(USE_MIRROR),cz)
YUM_REPOS?=proprietary
MIRROR_CENTOS?=http://mirror.seed-cz1.fuel-infra.org/fwm/$(PRODUCT_VERSION)/centos
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
YUM_REPOS?=official fuel subscr_manager
MIRROR_CENTOS?=http://mirrors-local-msk.msk.mirantis.net/centos-$(PRODUCT_VERSION)/$(CENTOS_RELEASE)
MIRROR_CENTOS_KERNEL?=http://mirror.centos.org/centos-6/6.6/
SANDBOX_MIRROR_CENTOS_UPSTREAM?=http://mirrors-local-msk.msk.mirantis.net/centos-$(PRODUCT_VERSION)/$(CENTOS_RELEASE)
SANDBOX_MIRROR_EPEL?=http://mirror.yandex.ru/epel/
MIRROR_UBUNTU_METHOD?=http
MIRROR_UBUNTU?=osci-mirror-msk.msk.mirantis.net
# := is used as a temporary solution to align this with jenkins-jobs
MIRROR_UBUNTU_ROOT:=/pkgs/ubuntu/
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
MIRROR_FUEL?=http://perestroika-repo-tst.infra.mirantis.net/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos6-fuel/os/x86_64

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
