define rhel_yum_conf
[main]
cachedir=$(BUILD_DIR)/mirror/rhel/cache
keepcache=0
debuglevel=6
logfile=$(BUILD_DIR)/mirror/rhel/yum.log
exclude=*.i686.rpm
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
pluginpath=$(BUILD_DIR)/mirror/rhel/etc/yum-plugins
pluginconfpath=$(BUILD_DIR)/mirror/rhel/etc/yum/pluginconf.d
reposdir=$(BUILD_DIR)/mirror/rhel/etc/yum.repos.d
endef

define rhel_yum_repo_rhel
[rhel-os-30-puddle]
name=OpenStack-3.0-Puddle
baseurl=http://srv11-msk.msk.mirantis.net/rhel6/OpenStack-3.0-Puddle
gpgcheck=0
enabled=1

[rhel-server-rpms]
name=rhel-6-server-rpms
baseurl=http://srv11-msk.msk.mirantis.net/rhel6/rhel-6-server-rpms
gpgcheck=0
enabled=1

[rhel-server-optional-rpms]
name=rhel-6-server-optional-rpms
baseurl=http://srv11-msk.msk.mirantis.net/rhel6/rhel-6-server-optional-rpms
gpgcheck=0
enabled=1

[rhel-ha-rpms]
name=rhel-ha-for-rhel-6-server-rpms
baseurl=http://srv11-msk.msk.mirantis.net/rhel6/rhel-ha-for-rhel-6-server-rpms
gpgcheck=0
enabled=1

[rhel-lb-rpms]
name=rhel-lb-for-rhel-6-server-rpms
baseurl=http://srv11-msk.msk.mirantis.net/rhel6/rhel-lb-for-rhel-6-server-rpms
gpgcheck=0
enabled=1

[rhel-rs-rpms]
name=rhel-rs-for-rhel-6-server-rpms
baseurl=http://srv11-msk.msk.mirantis.net/rhel6/rhel-rs-for-rhel-6-server-rpms
gpgcheck=0
enabled=1
endef 

define rhel_yum_repo_proprietary
[proprietary]
name = RHEL $(CENTOS_RELEASE) - Proprietary
baseurl = $(MIRROR_RHEL)
gpgcheck = 0
enabled = 1
priority=1
endef
