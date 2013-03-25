COMMIT_SHA:=$(shell git rev-parse --verify HEAD)
PRODUCT_VERSION:=1.0-rc1

CENTOS_MAJOR:=6
CENTOS_MINOR:=3
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
CENTOS_ARCH:=x86_64

NO_UI_OPTIMIZE:=0

LOCAL_MIRROR:=local_mirror
LOCAL_MIRROR_SRC:=$(LOCAL_MIRROR)/src
LOCAL_MIRROR_EGGS:=$(LOCAL_MIRROR)/eggs
LOCAL_MIRROR_GEMS:=$(LOCAL_MIRROR)/gems
LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)

# Use srv08 mirrors by default. Other possible default is 'msk'.
# Setting any other value or removing of this variable will cause
# download of all the packages directly from internet
USE_MIRROR:=srv08
ifeq ($(USE_MIRROR),srv08)
YUM_REPOS=proprietary
MIRROR_CENTOS=http://srv08-srt.srt.mirantis.net/fwm/centos
MIRROR_EGGS=http://srv08-srt.srt.mirantis.net/fwm/eggs
MIRROR_GEMS=http://srv08-srt.srt.mirantis.net/fwm/gems
MIRROR_SRC=http://srv08-srt.srt.mirantis.net/fwm/src
endif
ifeq ($(USE_MIRROR),msk)
YUM_REPOS=proprietary
MIRROR_CENTOS=http://172.18.8.209/fwm/centos
MIRROR_EGGS=http://172.18.8.209/fwm/eggs
MIRROR_GEMS=http://172.18.8.209/fwm/gems
MIRROR_SRC=http://172.18.8.209/fwm/src
endif

MIRROR_CENTOS?=http://mirror.yandex.ru/centos
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
YUM_REPOS?=official epel fuel_folsom puppetlabs rpmforge devel_puppetlabs

# Mirror of source packages. Bareword 'internet' is used to download packages
# directly from the internet
MIRROR_SRC?=internet

# INTEGRATION TEST CONFIG
NOFORWARD:=1
iso.path:=$(BUILD_DIR)/iso/nailgun-centos-6.3-amd64.iso
