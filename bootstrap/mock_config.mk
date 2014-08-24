define bootstrap-mock-site-defaults
# mock defaults
# vim:tw=0:ts=4:sw=4:et:
#
# This config file is for site-specific default values that apply across all
# configurations. Options specified in this config file can be overridden in
# the individual mock config files.
#
# The site-defaults.cfg delivered by default has NO options set. Only set
# options here if you want to override the defaults.
#
# Entries in this file follow the same format as other mock config files.
# config_opts['foo'] = bar
config_opts['plugin_conf']['ccache_enable'] = False

endef

BASE_PKGS:=shadow-utils \
	coreutils

define bootstrap-mock-fuel-config
config_opts['root'] = 'fuel-$(PRODUCT_VERSION)-bootstrap-$(CENTOS_ARCH)'
config_opts['target_arch'] = 'x86_64'
config_opts['chroot_setup_cmd'] = 'install -y $(BASE_PKGS)'

config_opts['yum.conf'] = """
[main]
cachedir=/var/cache/yum
keepcache=0
debuglevel=6
logfile=/var/log/yum.log
exclude=*.i686.rpm
exactarch=1
obsoletes=1
assumeyes=1
gpgcheck=0
plugins=1
pluginpath=/etc/yum-plugins
pluginconfpath=/etc/yum/pluginconf.d
reposdir=/etc/yum.repos.d
syslog_ident=mock
syslog_device=
exclude=ruby-2.1.1

[mirror]
name=Mirantis mirror
baseurl=file://$(LOCAL_MIRROR_CENTOS_OS_BASEURL)
gpgcheck=0
enabled=1

"""
endef

define bootstrap-mock-logging
[formatters]
keys: detailed,simple,unadorned,state

[handlers]
keys: simple_console,detailed_console,unadorned_console,simple_console_warnings_only

[loggers]
keys: root,build,state,mockbuild

[formatter_state]
format: %(asctime)s - %(message)s

[formatter_unadorned]
format: %(message)s

[formatter_simple]
format: %(levelname)s: %(message)s

;useful for debugging:
[formatter_detailed]
format: %(levelname)s %(filename)s:%(lineno)d:  %(message)s

[handler_unadorned_console]
class: StreamHandler
args: []
formatter: unadorned
level: INFO

[handler_simple_console]
class: StreamHandler
args: []
formatter: simple
level: INFO

[handler_simple_console_warnings_only]
class: StreamHandler
args: []
formatter: simple
level: WARNING

[handler_detailed_console]
class: StreamHandler
args: []
formatter: detailed
level: WARNING

; usually dont want to set a level for loggers
; this way all handlers get all messages, and messages can be filtered
; at the handler level
;
; all these loggers default to a console output handler
;
[logger_root]
level: NOTSET
handlers: simple_console

; mockbuild logger normally has no output
;  catches stuff like mockbuild.trace_decorator and mockbuild.util
;  dont normally want to propagate to root logger, either
[logger_mockbuild]
level: NOTSET
handlers:
qualname: mockbuild
propagate: 1

[logger_state]
level: NOTSET
; unadorned_console only outputs INFO or above
handlers: unadorned_console
qualname: mockbuild.Root.state
propagate: 0

[logger_build]
level: NOTSET
handlers: simple_console_warnings_only
qualname: mockbuild.Root.build
propagate: 0

; the following is a list mock logger qualnames used within the code:
;
;  qualname: mockbuild.util
;  qualname: mockbuild.uid
;  qualname: mockbuild.trace_decorator

endef

define bootstrap-install-modules
#!/bin/bash -x

rpm2cpio /var/tmp/$(KERNEL_PATTERN) | cpio -idm './lib/modules/*' './boot/vmlinuz*'
rpm2cpio /var/tmp/$(KERNEL_FIRMWARE_PATTERN) | cpio -idm './lib/firmware/*'
rpm2cpio /var/tmp/libmlx4* | cpio -idm './etc/*' './usr/lib64/*'

for version in `ls -1 /lib/modules`; do
	depmod $$version;
done

# Some extra actions
cp /sbin/init /init
endef

define bootstrap-customize-initram-root
#!/bin/bash -x

	# unpack custom files
	cd $(CHROOT_TMP) && tar -xzvf bootstrap-customize.tgz

	# fix permissions to root
	chown root:root -R $(CHROOT_TMP)

	# Copying custom files
	rsync -rlptDKv $(CHROOT_TMP)$(SOURCE_DIR)/bootstrap/sync/ /

	cp -r $(CHROOT_TMP)$(BUILD_DIR)/repos/nailgun/bin/send2syslog.py /usr/bin

	# Enabling pre-init boot interface discovery
	chkconfig setup-bootdev on

	# Setting root password into r00tme
	sed -i -e '/^root/croot:$$6$$oC7haQNQ$$LtVf6AI.QKn9Jb89r83PtQN9fBqpHT9bAFLzy.YVxTLiFgsoqlPY3awKvbuSgtxYHx4RUcpUqMotp.WZ0Hwoj.:15441:0:99999:7:::' /etc/shadow

	# Copying rsa key.
	mkdir -p /root/.ssh
	cp $(CHROOT_TMP)$(SOURCE_DIR)/bootstrap/ssh/id_rsa.pub /root/.ssh/authorized_keys
	chmod 700 /root/.ssh
	chmod 600 /root/.ssh/authorized_keys

	# Copying bash init files
	cp -f /etc/skel/.bash* /root/

	## Removing garbage
	# need also to remove mockbuild user and group

	# we also need to umount yum in chroot
	umount /var/cache/yum

	# then remove garbage
	rm -rf /home/*
	rm -rf \
		/var/cache/yum \
		/var/lib/yum \
		/usr/share/doc \
    /usr/share/locale \
		/tmp/* \
		/var/tmp/* \
		/builddir

endef
