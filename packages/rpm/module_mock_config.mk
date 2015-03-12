define rpm-mock-default
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

config_opts['plugin_conf']['tmpfs_enable'] = False
config_opts['plugin_conf']['tmpfs_opts']['required_ram_mb'] = 2048
config_opts['plugin_conf']['tmpfs_opts']['max_fs_size'] = '1024m'
config_opts['plugin_conf']['chroot_scan_enable'] = False

endef

define rpm-mock-config
config_opts['root'] = 'fuel-$(PRODUCT_VERSION)-$(CENTOS_ARCH)'
config_opts['target_arch'] = 'x86_64'
config_opts['chroot_setup_cmd'] = 'install bash ruby rpm-build tar python-setuptools shadow-utils python-pbr'
config_opts['cleanup_on_success'] = 0
config_opts['cleanup_on_failure'] = 0

config_opts['yum.conf'] = """
[main]
cachedir=/var/cache/yum
keepcache=0
debuglevel=6
logfile=/var/log/yum.log
exclude=*.i686.rpm
exactarch=1
obsoletes=1
gpgcheck=0
assumeyes=1
plugins=1
pluginpath=/etc/yum-plugins
pluginconfpath=/etc/yum/pluginconf.d
reposdir=/etc/yum.repos.d
syslog_ident=mock
syslog_device=

[mirror]
name=Mirantis mirror
baseurl=$(MOCK_MIRROR_CENTOS_OS_BASEURL)
gpgcheck=0
enabled=1

"""
endef

define rpm-mock-logging
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
