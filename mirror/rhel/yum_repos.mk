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

define rhel_yum_repo_proprietary
[proprietary]
name = RHEL $(CENTOS_RELEASE) - Proprietary
baseurl = $(MIRROR_RHEL)
gpgcheck = 0
enabled = 1
priority=1
endef
