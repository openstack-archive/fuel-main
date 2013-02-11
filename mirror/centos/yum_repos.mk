define yum_conf
[main]
cachedir=$(BUILD_DIR)/mirror/centos/cache
keepcache=0
debuglevel=6
logfile=$(BUILD_DIR)/mirror/centos/yum.log
exclude=*.i686.rpm
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
pluginpath=$(shell readlink -f -m $(BUILD_DIR)/mirror/centos/etc/yum-plugins)
pluginconfpath=$(shell readlink -f -m $(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d)
reposdir=$(BUILD_DIR)/mirror/centos/etc/yum.repos.d
endef


define yum_repo_centos
[base]
name=CentOS-$(CENTOS_RELEASE) - Base
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=os
baseurl=$(MIRROR_CENTOS)/$(CENTOS_RELEASE)/os/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
priority=10

[updates]
name=CentOS-$(CENTOS_RELEASE) - Updates
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=updates
baseurl=$(MIRROR_CENTOS)/$(CENTOS_RELEASE)/updates/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
priority=10

[extras]
name=CentOS-$(CENTOS_RELEASE) - Extras
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=extras
baseurl=$(MIRROR_CENTOS)/$(CENTOS_RELEASE)/extras/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
priority=10

[centosplus]
name=CentOS-$(CENTOS_RELEASE) - Plus
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=centosplus
baseurl=$(MIRROR_CENTOS)/$(CENTOS_RELEASE)/centosplus/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
priority=10

[contrib]
name=CentOS-$(CENTOS_RELEASE) - Contrib
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_RELEASE)&arch=$(CENTOS_ARCH)&repo=contrib
baseurl=$(MIRROR_CENTOS)/$(CENTOS_RELEASE)/contrib/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
priority=10
endef


define yum_repo_epel
[epel]
name=Extra Packages for Enterprise Linux $(CENTOS_MAJOR) - $(CENTOS_ARCH)
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-$(CENTOS_MAJOR)&arch=$(CENTOS_ARCH)
baseurl=http://mirror.yandex.ru/epel/$(CENTOS_MAJOR)/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
priority=20
endef

define yum_repo_fuel_folsom
[openstack-epel-fuel]
name=Mirantis OpenStack Custom Packages
mirrorlist=http://download.mirantis.com/epel-fuel-folsom/mirror.internal.list
gpgkey=https://fedoraproject.org/static/0608B895.txt
  http://mirror.centos.org/centos/RPM-GPG-KEY-CentOS-6
  http://download.mirantis.com/epel-fuel-folsom/rabbit.key
  http://download.mirantis.com/epel-fuel-folsom/mirantis.key
gpgcheck=0
enabled=1
priority=1
endef


define yum_repo_puppetlabs
[puppetlabs]
name=Puppet Labs Packages
baseurl=http://yum.puppetlabs.com/el/$(CENTOS_MAJOR)/products/$(CENTOS_ARCH)/
enabled=1
gpgcheck=1
gpgkey=http://yum.puppetlabs.com/RPM-GPG-KEY-puppetlabs
priority=1
endef


define yum_repo_rpmforge
[rpmforge]
name=RHEL $(CENTOS_RELEASE) - RPMforge.net - dag
#mirrorlist = http://apt.sw.be/redhat/el$(CENTOS_MAJOR)/en/mirrors-rpmforge
baseurl=http://apt.sw.be/redhat/el$(CENTOS_MAJOR)/en/$(CENTOS_ARCH)/rpmforge
gpgcheck=0
enabled=0

[rpmforge-extras]
name = RHEL $(CENTOS_RELEASE) - RPMforge.net - extras
#mirrorlist = http://apt.sw.be/redhat/el$(CENTOS_MAJOR)/en/mirrors-rpmforge-extras
baseurl = http://apt.sw.be/redhat/el$(CENTOS_MAJOR)/en/$(CENTOS_ARCH)/extras
gpgcheck = 0
enabled = 1
priority=95
endef


define yum_repo_mirantis
[mirror]
name=CentOS $(CENTOS_RELEASE) - Base
baseurl=http://srv08-srt.srt.mirantis.net/mirror/centos/$(CENTOS_RELEASE)/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
priority=1
endef
