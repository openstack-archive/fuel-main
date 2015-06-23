define yum_conf
[main]
cachedir=$(BUILD_DIR)/mirror/centos/cache
keepcache=0
debuglevel=6
logfile=$(BUILD_DIR)/mirror/centos/yum.log
exclude=*.i686.rpm ntp-dev*
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
priority=90

[updates]
name=CentOS-$(CENTOS_RELEASE) - Updates
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=updates
baseurl=$(MIRROR_CENTOS)/updates/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
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
