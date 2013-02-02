COMMIT_SHA:=$(shell git rev-parse --verify HEAD)

CENTOS_MAJOR:=6
CENTOS_MINOR:=3
CENTOS_RELEASE:=$(CENTOS_MAJOR).$(CENTOS_MINOR)
CENTOS_ARCH:=x86_64

LOCAL_MIRROR:=local_mirror
LOCAL_MIRROR_SRC:=$(LOCAL_MIRROR)/src
LOCAL_MIRROR_EGGS:=$(LOCAL_MIRROR)/eggs
LOCAL_MIRROR_GEMS:=$(LOCAL_MIRROR)/gems
LOCAL_MIRROR_CENTOS:=$(LOCAL_MIRROR)/centos
LOCAL_MIRROR_CENTOS_OS_BASEURL:=$(LOCAL_MIRROR_CENTOS)/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)

MIRROR_CENTOS:=http://mirror.yandex.ru/centos
MIRROR_CENTOS_OS_BASEURL:=$(MIRROR_CENTOS)/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)
# It can be any a list of links (--find-links) or a pip index (--index-url).
MIRROR_EGGS:=http://pypi.python.org/simple
# NOTE(mihgen): removed gemcutter - it redirects to rubygems.org and has issues w/certificate now
MIRROR_GEMS:=http://rubygems.org http://gems.rubyforge.org

REQUIRED_RPMS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-rpm.txt)
RPMFORGE_RPMS:=qemu
REQUIRED_EGGS:=$(shell grep -v "^\\s*\#" $(SOURCE_DIR)/requirements-eggs.txt)
REQUIRED_SRCS:=$(shell grep -v ^\\s*\# $(SOURCE_DIR)/requirements-src.txt)

# Which repositories to use for making local centos mirror.
# Possible values you can find out from mirror/centos/yum_repos.mk file.
# The actual name will be constracted wich prepending "yum_repo_" prefix.
# Example: YUM_REPOS:=centos epel => yum_repo_centos and yum_repo_epel
# will be used.
YUM_REPOS:=centos epel fuel_folsom puppetlabs rpmforge


# INTEGRATION TEST CONFIG
NOFORWARD:=1
iso.path:=$(BUILD_DIR)/iso/nailgun-centos-6.3-amd64.iso
