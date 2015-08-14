
# Problem: --archlist=x86_64 really means "x86_64 and i686". Therefore yum
# tries to resolve dependencies of i686 packages. Sometimes this fails due
# to an upgraded x86_64 only package available in the fuel repo. For
# instance, when yum is asked to download dmraid package it tries to resolve
# the dependencies of i686 version. This fails since the upgraded
# device-mapper-libs package (from the fuel repo) is x86_64 only:
# Package: device-mapper-libs-1.02.79-8.el6.i686 (base)
#   Requires: device-mapper = 1.02.79-8.el6
#   Available: device-mapper-1.02.79-8.el6.x86_64 (base)
#     device-mapper = 1.02.79-8.el6
#   Installing: device-mapper-1.02.90-2.mira1.x86_64 (fuel)
#        device-mapper = 1.02.90-2.mira1
# The obvious solution is to exclude i686 packages. However syslinux
# package depends on i686 package syslinux-nonlinux (which contians
# the binaries that run in the syslinux environment). Since excluding
# packages by regexp is impossible (only glob patterns are supported)
# base and updates repos are "cloned". Those "cloned" repos contain
# a few whitelisted i686 packages (for now only syslinux).
# Note: these packages should be also excluded from base and updates.
x86_rpm_packages_whitelist:=syslinux*

define yum_conf
[main]
cachedir=$(BUILD_DIR)/mirror/centos/cache
keepcache=0
debuglevel=6
logfile=$(BUILD_DIR)/mirror/centos/yum.log
exclude=ntp-dev*
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
pluginpath=$(BUILD_DIR)/mirror/centos/etc/yum-plugins
pluginconfpath=$(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d
reposdir=$(BUILD_DIR)/mirror/centos/etc/yum.repos.d
endef

define yum_repo_official
[base]
name=CentOS-$(CENTOS_RELEASE) - Base
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=os
baseurl=$(MIRROR_CENTOS)/os/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
exclude=*i686 $(x86_rpm_packages_whitelist)
priority=90

[updates]
name=CentOS-$(CENTOS_RELEASE) - Updates
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=updates
baseurl=$(MIRROR_CENTOS)/updates/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
exclude=*i686 $(x86_rpm_packages_whitelist)
priority=90

[base_i686_whitelisted]
name=CentOS-$(CENTOS_RELEASE) - Base
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=os
baseurl=$(MIRROR_CENTOS)/os/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
includepkgs=$(x86_rpm_packages_whitelist)
priority=90

[updates_i686_whitelisted]
name=CentOS-$(CENTOS_RELEASE) - Updates
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=updates
baseurl=$(MIRROR_CENTOS)/updates/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
includepkgs=$(x86_rpm_packages_whitelist)
priority=90

[extras]
name=CentOS-$(CENTOS_RELEASE) - Extras
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=extras
baseurl=$(MIRROR_CENTOS)/extras/$(CENTOS_ARCH)
gpgcheck=0
enabled=0
priority=90

[centosplus]
name=CentOS-$(CENTOS_RELEASE) - Plus
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=centosplus
baseurl=$(MIRROR_CENTOS)/centosplus/$(CENTOS_ARCH)
gpgcheck=0
enabled=0
priority=90

[contrib]
name=CentOS-$(CENTOS_RELEASE) - Contrib
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=contrib
baseurl=$(MIRROR_CENTOS)/contrib/$(CENTOS_ARCH)
gpgcheck=0
enabled=0
priority=90
endef

define yum_repo_fuel
[fuel]
name=Mirantis OpenStack Custom Packages
#mirrorlist=http://download.mirantis.com/epel-fuel-grizzly-3.1/mirror.internal.list
baseurl=$(MIRROR_FUEL)
gpgcheck=0
enabled=1
priority=20
endef

define yum_repo_proprietary
[proprietary]
name = CentOS $(CENTOS_RELEASE) - Proprietary
baseurl = $(MIRROR_CENTOS)/os/$(CENTOS_ARCH)
gpgcheck = 0
enabled = 1
priority=20
endef

define yum_repo_release
[release]
name = CentOS $(CENTOS_RELEASE) - Release $(PRODUCT_VERSION)
baseurl = $(RELEASE_CENTOS_MIRROR)
gpgcheck = 0
enabled = 1
priority=30
endef

# Accept EXTRA_RPM_REPOS in a form of a list of: name,url,priority
# Accept EXTRA_RPM_REPOS in a form of list of (default priority=10): name,url
get_repo_name=$(shell echo $1 | cut -d ',' -f 1)
get_repo_url=$(shell echo $1 | cut -d ',' -f2)
get_repo_priority=$(shell val=`echo $1 | cut -d ',' -f3`; echo $${val:-10})

# It's a callable object.
# Usage: $(call create_extra_repo,repo)
# where:
# repo=repo_name,http://path_to_the_repo,repo_priority
# repo_priority is a number from 1 to 99
define create_extra_repo
[$(call get_repo_name,$1)]
name = Repo "$(call get_repo_name,$1)"
baseurl = $(call get_repo_url,$1)
gpgcheck = 0
enabled = 1
priority = $(call get_repo_priority,$1)
endef
