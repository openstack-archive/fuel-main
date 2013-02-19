module Astute
  module LogParser
    module Patterns
      def self.get_default_pattern(key)
        return Marshal.load(Marshal.dump(@default_patterns[key]))
      end

      def self.list_default_patterns
        return @default_patterns.keys
      end

      @default_patterns = {
        'anaconda-log-supposed-time-baremetal' => # key for default baremetal provision pattern
          {'type' => 'supposed-time',
          'chunk_size' => 10000,
          'date_format' => '%Y-%m-%dT%H:%M:%S',
          'date_regexp' => '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
          'pattern_list' => [
            {'pattern' => 'Running anaconda script', 'supposed_time' => 60},
            {'pattern' => 'moving (1) to step enablefilesystems', 'supposed_time' => 3},
            {'pattern' => "notifying kernel of 'change' event on device", 'hdd_size_multiplier' => 0.3},
            {'pattern' => 'Preparing to install packages', 'supposed_time' => 9},
            {'pattern' => 'Installing glibc-common-2.12', 'supposed_time' => 9},
            {'pattern' => 'Installing bash-4.1.2', 'supposed_time' => 11},
            {'pattern' => 'Installing coreutils-8.4-19', 'supposed_time' => 20},
            {'pattern' => 'Installing centos-release-6-3', 'supposed_time' => 21},
            {'pattern' => 'Installing attr-2.4.44', 'supposed_time' => 23},
            {'pattern' => 'leaving (1) step installpackages', 'supposed_time' => 60},
            {'pattern' => 'moving (1) to step postscripts', 'supposed_time' => 4},
            {'pattern' => 'leaving (1) step postscripts', 'supposed_time' => 130},
            {'pattern' => 'wait while node rebooting', 'supposed_time' => 20},
            ].reverse,
          'filename' => 'install/anaconda.log'
          },

        'anaconda-log-supposed-time-kvm' => # key for default kvm provision pattern
          {'type' => 'supposed-time',
          'chunk_size' => 10000,
          'date_format' => '%Y-%m-%dT%H:%M:%S',
          'date_regexp' => '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
          'pattern_list' => [
            {'pattern' => 'Running anaconda script', 'supposed_time' => 60},
            {'pattern' => 'moving (1) to step enablefilesystems', 'supposed_time' => 3},
            {'pattern' => "notifying kernel of 'change' event on device", 'hdd_size_multiplier' => 1.5},
            {'pattern' => 'Preparing to install packages', 'supposed_time' => 12},
            {'pattern' => 'Installing glibc-common-2.12', 'supposed_time' => 15},
            {'pattern' => 'Installing bash-4.1.2', 'supposed_time' => 15},
            {'pattern' => 'Installing coreutils-8.4-19', 'supposed_time' => 33},
            {'pattern' => 'Installing centos-release-6-3', 'supposed_time' => 21},
            {'pattern' => 'Installing attr-2.4.44', 'supposed_time' => 48},
            {'pattern' => 'leaving (1) step installpackages', 'supposed_time' => 100},
            {'pattern' => 'moving (1) to step postscripts', 'supposed_time' => 4},
            {'pattern' => 'leaving (1) step postscripts', 'supposed_time' => 200},
            {'pattern' => 'wait while node rebooting', 'supposed_time' => 20},
            ].reverse,
          'filename' => 'install/anaconda.log'
          },

        'puppet-log-components-list-ha_compute-controller' =>   # key for default HA deploy pattern
          {'type' => 'components-list',
          'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
          'chunk_size' => 40000,
          'filename' => 'puppet-agent.log',
          'components_list' => [
            {'name' => 'Galera', 'weight' => 5, 'patterns' => [
               {'pattern' => '/Stage[main]/Galera/File[/etc/mysql]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Galera/Package[galera]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Galera/Package[MySQL-client]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Galera/Package[MySQL-server]/ensure) created', 'progress' => 0.6},
               {'pattern' => "/Stage[main]/Galera/Service[mysql-galera]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Galera/Exec[wait-for-synced-state]/returns) executed successfully', 'progress' => 0.9},
               {'pattern' => '/Stage[main]/Galera::Galera_master_final_config/Exec'\
                             '[first-galera-node-final-config]/returns) executed successfully', 'progress' => 1},
               ]
            },
            {'name' => 'Glance', 'weight' => 5, 'patterns' => [
               {'pattern' => '/Stage[main]/Glance/Package[glance]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Glance::Db::Mysql/Mysql::Db[glance]/Database[glance]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Glance::Db::Mysql/Glance::Db::Mysql::Host_access[]/'\
                             'Database_user[glance@]/ensure) created', 'progress' => 0.7},
               {'pattern' => '/Stage[main]/Glance::Registry/Glance_registry_config[keystone_authtoken/'\
                             'admin_user]/value) value changed', 'progress' => 0.71},
               {'pattern' => '/Stage[main]/Glance::Keystone::Auth/Keystone_endpoint[glance]/ensure) created', 'progress' => 0.8},
               {'pattern' => "/Stage[main]/Glance::Registry/Service[glance-registry]/ensure)"\
                             " ensure changed 'stopped' to 'running'", 'progress' => 0.95},
               {'pattern' => "/Stage[main]/Glance::Api/Service[glance-api]/ensure) ensure changed"\
                             " 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Haproxy', 'weight' => 5, 'patterns' => [
               {'pattern' => '/Stage[main]/Haproxy/Concat[/etc/haproxy/haproxy.cfg]/File[/var/lib/puppet/'\
                             'concat/_etc_haproxy_haproxy.cfg]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Haproxy/Concat[/etc/haproxy/haproxy.cfg]/File[/var/lib/puppet/'\
                             'concat/_etc_haproxy_haproxy.cfg/fragments.concat.out]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Haproxy/Concat[/etc/haproxy/haproxy.cfg]/Exec[concat_/etc/haproxy/'\
                             'haproxy.cfg]/returns) executed successfully', 'progress' => 0.8},
               {'pattern' => "/Stage[main]/Haproxy/Service[haproxy]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Horizon', 'weight' => 5, 'patterns' => [
               {'pattern' => '/Stage[main]/Horizon/Package[mod_wsgi]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Horizon/Package[openstack-dashboard]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Horizon/File[/etc/openstack-dashboard/'\
                             'local_settings]/content) content changed', 'progress' => 0.8},
               {'pattern' => "/Stage[main]/Horizon/Service[\$::horizon::params::http_service]/"\
                             "ensure) ensure changed 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Keepalived', 'weight' => 1, 'patterns' => [
               {'pattern' => '/Stage[main]/Keepalived::Install/Package[keepalived]/ensure) created', 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Keepalived::Config/Concat[/etc/keepalived/keepalived.conf]/'\
                             'File[/etc/keepalived/keepalived.conf]/content) content changed', 'progress' => 0.6},
               {'pattern' => "/Stage[main]/Keepalived::Service/Service[keepalived]/ensure) ensure"\
                             " changed 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Keystone', 'weight' => 1, 'patterns' => [
               {'pattern' => '/Stage[main]/Keystone::Python/Package[python-keystone]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Keystone::Db::Mysql/Mysql::Db[keystone]/Database[keystone]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Keystone/Package[keystone]/ensure) created', 'progress' => 0.6},
               {'pattern' => '/Stage[main]/Keystone/Keystone_config[DEFAULT/admin_port]/ensure) created', 'progress' => 0.7},
               {'pattern' => "/Stage[main]/Keystone/Service[keystone]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Keystone::Roles::Admin/Keystone_user_role[admin@admin]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Memcached', 'weight' => 1, 'patterns' => [
               {'pattern' => '/Stage[main]/Memcached/User[memcached]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Memcached/Package[memcached]/ensure) created', 'progress' => 0.4},
               {'pattern' => "/Stage[main]/Memcached/Service[memcached]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Rabbitmq', 'weight' => 1, 'patterns' => [
               {'pattern' => '/Stage[main]/Rabbitmq::Server/Package[rabbitmq-server]/ensure) created', 'progress' => 0.3},
               {'pattern' => "/Stage[main]/Rabbitmq::Service/Service[rabbitmq-server]/ensure) ensure changed 'stopped' to 'running", 'progress' => 0.7},
               {'pattern' => '/Stage[main]/Rabbitmq::Server/Rabbitmq_user[guest]/ensure) removed', 'progress' => 1},
               ]
            },
            {'name' => 'Rsync/Xinetd', 'weight' => 1, 'patterns' => [
               {'pattern' => '/Stage[main]/Xinetd/Package[xinetd]/ensure) created', 'progress' => 0.2},
               {'pattern' => '(/Stage[main]/Xinetd/File[/etc/xinetd.conf]/content) content changed', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Rsync::Server/File[/etc/rsync.d]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Rsync::Server/Xinetd::Service[rsync]/File[/etc/xinetd.d/rsync]/content) content changed', 'progress' => 1},
               ]
            },
            {'name' => 'Swift', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Swift::Xfs/Package[xfsprogs]/ensure) created', 'progress' => 0.01},
               {'pattern' => '/Stage[main]/Swift/File[/etc/swift/swift.conf]/content) content changed', 'progress' => 0.05},
               {'pattern' => '/Stage[main]/Swift/File[/home/swift]/ensure) created', 'progress' => 0.07},
               {'pattern' => '/Stage[main]/Swift::Storage::All/File[/srv/node]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Swift::Storage::Account/Swift::Storage::Generic[account]/File'\
                             '[/etc/swift/account-server/]/ensure) created', 'progress' => 0.12},
               {'pattern' => '/Stage[main]/Swift::Storage::Object/Swift::Storage::Generic[object]/Package'\
                             '[swift-object]/ensure) created', 'progress' => 0.15},
               {'pattern' => "/Stage[main]/Swift::Storage::Account/Swift::Storage::Generic[account]/Service"\
                             "[swift-account]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 0.18},
               {'pattern' => "/Stage[main]/Swift::Storage::Object/Swift::Storage::Generic[object]/Service"\
                             "[swift-object]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Swift::Keystone::Auth/Keystone_service[swift]/ensure) created', 'progress' => 0.23},
               {'pattern' => '/Stage[main]/Swift::Keystone::Auth/Keystone_user_role[swift@services]/ensure) created', 'progress' => 0.28},
               {'pattern' => '/Stage\[main\]/Swift::Storage::Container/Ring_container_device\[[0-9.:]+\]/ensure\) created',
                             'regexp' => true, 'progress' => 0.33},
               {'pattern' => "/Stage[main]/Swift::Storage::Account/Swift::Storage::Generic[account]/File[/etc/swift/"\
                             "account-server/]/group) group changed 'root' to 'swift'", 'progress' => 0.36},
               {'pattern' => '/Stage[main]/Swift::Ringbuilder/Swift::Ringbuilder::Rebalance[object]/Exec'\
                             '[hours_passed_object]/returns) executed successfully', 'progress' => 0.39},
               {'pattern' => '/Stage[main]/Swift::Ringbuilder/Swift::Ringbuilder::Rebalance[account]/Exec'\
                             '[hours_passed_account]/returns) executed successfully', 'progress' => 0.42},
               {'pattern' => '/Stage[main]/Swift::Ringbuilder/Swift::Ringbuilder::Rebalance[account]/Exec'\
                             '[rebalance_account]/returns) executed successfully', 'progress' => 0.44},
               {'pattern' => '/Stage[main]/Swift::Ringbuilder/Swift::Ringbuilder::Rebalance[container]/Exec'\
                             '[hours_passed_container]/returns) executed successfully', 'progress' => 0.49},
               {'pattern' => '/Stage[main]/Swift::Ringbuilder/Swift::Ringbuilder::Rebalance[container]/Exec'\
                             '[rebalance_container]/returns) executed successfully', 'progress' => 0.52},
               {'pattern' => '/Stage[main]/Swift::Proxy/Package[swift-proxy]/ensure) created', 'progress' => 0.55},
               {'pattern' => '/Service[swift-container-replicator]/ensure) ensure changed \'stopped\'', 'progress' => 0.9},
               {'pattern' => '/Service[swift-accaunt-replicator]/ensure) ensure changed \'stopped\'', 'progress' => 0.95},
               {'pattern' => '/Service[swift-object-replicator]/ensure) ensure changed \'stopped\'', 'progress' => 1},
               ]
            },
            {'name' => 'Nova', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[euca2ools]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[parted]/ensure) created', 'progress' => 0.11},
               {'pattern' => '/Stage[main]/Nova::Api/Nova::Generic_service[api]/Package[nova-api]/ensure) created', 'progress' => 0.13},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[unzip]/ensure) created', 'progress' => 0.15},
               {'pattern' => '/Stage[main]/Nova::Vncproxy/Package[python-numpy]/ensure) created', 'progress' => 0.2},
               {'pattern' => '(/Stage[main]/Nova::Utilities/Package[libguestfs-tools-c]/ensure) created', 'progress' => 0.25},
               {'pattern' => '/Stage[main]/Nova::Rabbitmq/Rabbitmq_user_permissions[nova@/]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Nova::Db::Mysql/Mysql::Db[nova]/Database[nova]/ensure) created', 'progress' => 0.35},
               {'pattern' => "/Stage[main]/Nova::Db::Mysql/Mysql::Db[nova]/Database_grant"\
                             "[nova@127.0.0.1/nova]/privileges) privileges changed '' to 'all'", 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Nova::Vncproxy/Nova::Generic_service[vncproxy]/Package'\
                             '[nova-vncproxy]/ensure) created', 'progress' => 0.45},
               {'pattern' => '/Stage[main]/Nova::Keystone::Auth/Keystone_service[nova_volume]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Nova::Keystone::Auth/Keystone_user_role[nova@services]/ensure) created', 'progress' => 0.55},
               {'pattern' => '/Stage[main]/Nova/Exec[post-nova_config]/returns) Nova config has changed', 'progress' => 0.6},
               {'pattern' => '/Stage[main]/Nova::Api/Exec[nova-db-sync]/returns) executed successfully', 'progress' => 0.7},
               {'pattern' => "/Stage[main]/Nova::Consoleauth/Nova::Generic_service[consoleauth]/Service"\
                             "[nova-consoleauth]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 0.85},
               {'pattern' => '/Stage[main]/Nova::Network/Nova::Manage::Network[nova-vm-net]/Nova_network'\
                             'nova-vm-net]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Openstack', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Openstack::Firewall/File[iptables]/ensure) defined content as', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Openstack::Glance/Package[swift]/ensure) created', 'progress' => 0.15},
               {'pattern' => '/Stage[main]/Openstack::Auth_file/File[/root/openrc]/ensure) defined content as', 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Openstack::Controller_ha/Package[socat]/ensure) created', 'progress' => 0.25},
               {'pattern' => '/Stage[main]/Openstack::Swift::Storage-node/Swift::Storage::Loopback[1]/File[/srv/loopback-device]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Openstack::Controller_ha/Exec[wait-for-haproxy-mysql-backend]/returns) executed successfully', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Openstack::Controller/Nova_config[DEFAULT/memcached_servers]/ensure) created', 'progress' => 0.45},
               {'pattern' => '/Stage[main]/Openstack::Nova::Controller/Nova_config[DEFAULT/multi_host]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Openstack::Firewall/Exec[startup-firewall]/returns) executed successfully', 'progress' => 0.65},
               {'pattern' => '/Stage[main]/Openstack::Swift::Proxy/Ring_object_device\[[0-9.:]+\]/ensure\) created',
                             'regexp' => true, 'progress' => 0.75},
               {'pattern' => '/Stage[main]/Openstack::Swift::Proxy/Ring_container_device\[[0-9.:]+\]/ensure\) created',
                             'regexp' => true, 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Openstack::Img::Cirros/Package[cirros-testvm]/ensure) created', 'progress' => 1},
               ]
            },
            ]
          },

        'puppet-log-components-list-ha_compute-compute' =>
          {'type' => 'components-list',
          'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
          'chunk_size' => 40000,
          'filename' => 'puppet-agent.log',
          'components_list' => [
            {'name' => 'Keystone', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Keystone::Python/Package[python-keystone]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Mysql', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Mysql::Python/Package[python-mysqldb]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Nova', 'weight' => 5, 'patterns' => [
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[euca2ools]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[parted]/ensure) created', 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Nova::Api/Nova::Generic_service[api]/Package[nova-api]/ensure) created', 'progress' => 0.28},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[unzip]/ensure) created', 'progress' => 0.32},
               {'pattern' => '/Stage[main]/Nova::Vncproxy/Package[python-numpy]/ensure) created', 'progress' => 0.35},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[libguestfs-tools-c]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Nova::Rabbitmq/Rabbitmq_user_permissions[nova@/]/ensure) created', 'progress' => 0.43},
               {'pattern' => '/Stage[main]/Nova/Exec[post-nova_config]/returns) Nova config has changed', 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Nova::Api/Exec[nova-db-sync]/returns) executed successfully', 'progress' => 0.85},
               {'pattern' => '/Stage[main]/Nova::Network/Nova::Manage::Network[nova-vm-net]/Nova_network'\
                             'nova-vm-net]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Nova::Compute', 'weight' => 15, 'patterns' => [
               {'pattern' => '/Stage[main]/Nova::Compute/Package[bridge-utils]/ensure) created', 'progress' => 0.15},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Exec[symlink-qemu-kvm]/returns) executed successfully', 'progress' => 0.25},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Package[libvirt]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Package[dnsmasq-utils]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Nova_config[DEFAULT/vncserver_listen]/ensure) created', 'progress' => 0.55},
               {'pattern' => '/Stage[main]/Nova::Compute/Nova::Generic_service[compute]/Package[nova-compute]/ensure) created', 'progress' => 0.88},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Package[avahi]/ensure) created', 'progress' => 0.9},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Service[messagebus]/ensure) ensure changed', 'progress' => 0.93},
               {'pattern' => '/Stage[main]/Nova::Compute/Nova::Generic_service[compute]/Service[nova-compute]/ensure) ensure changed', 'progress' => 0.97},
               {'pattern' => '/Stage[main]/Nova::Compute/Nova::Generic_service[compute]/Service[nova-compute]) Triggered', 'progress' => 1},
               ]
            },
            {'name' => 'Openstack', 'weight' => 2, 'patterns' => [
               {'pattern' => '/Stage[main]/Openstack::Compute/Nova_config[DEFAULT/metadata_host]/ensure) created', 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Openstack::Compute/Nova_config[DEFAULT/memcached_servers]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Openstack::Compute/Augeas[sysconfig-libvirt]/returns) executed successfully', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Openstack::Compute/Nova_config[DEFAULT/multi_host]/ensure) created', 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Openstack::Compute/Augeas[libvirt-conf]/returns) executed successfully', 'progress' => 1},
               ]
            },
            ]
          },

        'puppet-log-components-list-singlenode_compute-controller' =>
          {'type' => 'components-list',
          'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
          'chunk_size' => 40000,
          'filename' => 'puppet-agent.log',
          'components_list' => [
            {'name' => 'Glance', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Glance/Package[glance]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Glance::Db::Mysql/Mysql::Db[glance]/Database[glance]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Glance::Db::Mysql/Glance::Db::Mysql::Host_access[]/'\
                             'Database_user[glance@]/ensure) created', 'progress' => 0.7},
               {'pattern' => '/Stage[main]/Glance::Registry/Glance_registry_config[keystone_authtoken/'\
                             'admin_user]/value) value changed', 'progress' => 0.71},
               {'pattern' => '/Stage[main]/Glance::Keystone::Auth/Keystone_endpoint[glance]/ensure) created', 'progress' => 0.8},
               {'pattern' => "/Stage[main]/Glance::Registry/Service[glance-registry]/ensure)"\
                             " ensure changed 'stopped' to 'running'", 'progress' => 0.95},
               {'pattern' => "/Stage[main]/Glance::Api/Service[glance-api]/ensure) ensure changed"\
                             " 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Horizon', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Horizon/Package[mod_wsgi]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Horizon/Package[openstack-dashboard]/ensure) created', 'progress' => 0.6},
               {'pattern' => '/Stage[main]/Horizon/File[/etc/openstack-dashboard/'\
                             'local_settings]/content) content changed', 'progress' => 0.8},
               {'pattern' => "/Stage[main]/Horizon/Service[\$::horizon::params::http_service]/"\
                             "ensure) ensure changed 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Keystone', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Keystone::Python/Package[python-keystone]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Keystone::Db::Mysql/Mysql::Db[keystone]/Database[keystone]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Keystone/Package[keystone]/ensure) created', 'progress' => 0.6},
               {'pattern' => '/Stage[main]/Keystone/Keystone_config[DEFAULT/admin_port]/ensure) created', 'progress' => 0.7},
               {'pattern' => "/Stage[main]/Keystone/Service[keystone]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Keystone::Roles::Admin/Keystone_user_role[admin@admin]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Memcached', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Memcached/User[memcached]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Memcached/Package[memcached]/ensure) created', 'progress' => 0.6},
               {'pattern' => "/Stage[main]/Memcached/Service[memcached]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Rabbitmq', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Rabbitmq::Server/Package[rabbitmq-server]/ensure) created', 'progress' => 0.3},
               {'pattern' => "/Stage[main]/Rabbitmq::Service/Service[rabbitmq-server]/ensure) ensure changed 'stopped' to 'running", 'progress' => 0.7},
               {'pattern' => '/Stage[main]/Rabbitmq::Server/Rabbitmq_user[guest]/ensure) removed', 'progress' => 1},
               ]
            },
            {'name' => 'Nova', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[euca2ools]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[parted]/ensure) created', 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Nova::Api/Nova::Generic_service[api]/Package[nova-api]/ensure) created', 'progress' => 0.28},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[unzip]/ensure) created', 'progress' => 0.32},
               {'pattern' => '/Stage[main]/Nova::Vncproxy/Package[python-numpy]/ensure) created', 'progress' => 0.35},
               {'pattern' => '(/Stage[main]/Nova::Utilities/Package[libguestfs-tools-c]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Nova::Rabbitmq/Rabbitmq_user_permissions[nova@/]/ensure) created', 'progress' => 0.43},
               {'pattern' => '/Stage[main]/Nova::Db::Mysql/Mysql::Db[nova]/Database[nova]/ensure) created', 'progress' => 0.48},
               {'pattern' => "/Stage[main]/Nova::Db::Mysql/Mysql::Db[nova]/Database_grant"\
                             "[nova@127.0.0.1/nova]/privileges) privileges changed '' to 'all'", 'progress' => 0.51},
               {'pattern' => '/Stage[main]/Nova::Vncproxy/Nova::Generic_service[vncproxy]/Package'\
                             '[nova-vncproxy]/ensure) created', 'progress' => 0.6},
               {'pattern' => '/Stage[main]/Nova::Keystone::Auth/Keystone_service[nova_volume]/ensure) created', 'progress' => 0.68},
               {'pattern' => '/Stage[main]/Nova::Keystone::Auth/Keystone_user_role[nova@services]/ensure) created', 'progress' => 0.75},
               {'pattern' => '/Stage[main]/Nova/Exec[post-nova_config]/returns) Nova config has changed', 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Nova::Api/Exec[nova-db-sync]/returns) executed successfully', 'progress' => 0.85},
               {'pattern' => "/Stage[main]/Nova::Consoleauth/Nova::Generic_service[consoleauth]/Service"\
                             "[nova-consoleauth]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 0.9},
               {'pattern' => '/Stage[main]/Nova::Network/Nova::Manage::Network[nova-vm-net]/Nova_network'\
                             'nova-vm-net]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Openstack', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Openstack::Firewall/File[iptables]/ensure) defined content as', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Openstack::Glance/Package[swift]/ensure) created', 'progress' => 0.15},
               {'pattern' => '/Stage[main]/Openstack::Auth_file/File[/root/openrc]/ensure) defined content as', 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Openstack::Controller/Nova_config[DEFAULT/memcached_servers]/ensure) created', 'progress' => 0.45},
               {'pattern' => '/Stage[main]/Openstack::Nova::Controller/Nova_config[DEFAULT/multi_host]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Openstack::Firewall/Exec[startup-firewall]/returns) executed successfully', 'progress' => 0.65},
               {'pattern' => '/Stage[main]/Openstack::Img::Cirros/Package[cirros-testvm]/ensure) created', 'progress' => 1},
               ]
            },
            ]
          },

        'puppet-log-components-list-multinode_compute-controller' =>
          {'type' => 'components-list',
          'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
          'chunk_size' => 40000,
          'filename' => 'puppet-agent.log',
          'components_list' => [
            {'name' => 'Glance', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Glance/Package[glance]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Glance::Db::Mysql/Mysql::Db[glance]/Database[glance]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Glance::Db::Mysql/Glance::Db::Mysql::Host_access[]/'\
                             'Database_user[glance@]/ensure) created', 'progress' => 0.7},
               {'pattern' => '/Stage[main]/Glance::Registry/Glance_registry_config[keystone_authtoken/'\
                             'admin_user]/value) value changed', 'progress' => 0.71},
               {'pattern' => '/Stage[main]/Glance::Keystone::Auth/Keystone_endpoint[glance]/ensure) created', 'progress' => 0.8},
               {'pattern' => "/Stage[main]/Glance::Registry/Service[glance-registry]/ensure)"\
                             " ensure changed 'stopped' to 'running'", 'progress' => 0.95},
               {'pattern' => "/Stage[main]/Glance::Api/Service[glance-api]/ensure) ensure changed"\
                             " 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Horizon', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Horizon/Package[mod_wsgi]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Horizon/Package[openstack-dashboard]/ensure) created', 'progress' => 0.6},
               {'pattern' => '/Stage[main]/Horizon/File[/etc/openstack-dashboard/'\
                             'local_settings]/content) content changed', 'progress' => 0.8},
               {'pattern' => "/Stage[main]/Horizon/Service[\$::horizon::params::http_service]/"\
                             "ensure) ensure changed 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Keystone', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Keystone::Python/Package[python-keystone]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Keystone::Db::Mysql/Mysql::Db[keystone]/Database[keystone]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Keystone/Package[keystone]/ensure) created', 'progress' => 0.6},
               {'pattern' => '/Stage[main]/Keystone/Keystone_config[DEFAULT/admin_port]/ensure) created', 'progress' => 0.7},
               {'pattern' => "/Stage[main]/Keystone/Service[keystone]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Keystone::Roles::Admin/Keystone_user_role[admin@admin]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Memcached', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Memcached/User[memcached]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Memcached/Package[memcached]/ensure) created', 'progress' => 0.6},
               {'pattern' => "/Stage[main]/Memcached/Service[memcached]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 1},
               ]
            },
            {'name' => 'Rabbitmq', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Rabbitmq::Server/Package[rabbitmq-server]/ensure) created', 'progress' => 0.3},
               {'pattern' => "/Stage[main]/Rabbitmq::Service/Service[rabbitmq-server]/ensure) ensure changed 'stopped' to 'running", 'progress' => 0.7},
               {'pattern' => '/Stage[main]/Rabbitmq::Server/Rabbitmq_user[guest]/ensure) removed', 'progress' => 1},
               ]
            },
            {'name' => 'Nova', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[euca2ools]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[parted]/ensure) created', 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Nova::Api/Nova::Generic_service[api]/Package[nova-api]/ensure) created', 'progress' => 0.28},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[unzip]/ensure) created', 'progress' => 0.32},
               {'pattern' => '/Stage[main]/Nova::Vncproxy/Package[python-numpy]/ensure) created', 'progress' => 0.35},
               {'pattern' => '(/Stage[main]/Nova::Utilities/Package[libguestfs-tools-c]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Nova::Rabbitmq/Rabbitmq_user_permissions[nova@/]/ensure) created', 'progress' => 0.43},
               {'pattern' => '/Stage[main]/Nova::Db::Mysql/Mysql::Db[nova]/Database[nova]/ensure) created', 'progress' => 0.48},
               {'pattern' => "/Stage[main]/Nova::Db::Mysql/Mysql::Db[nova]/Database_grant"\
                             "[nova@127.0.0.1/nova]/privileges) privileges changed '' to 'all'", 'progress' => 0.51},
               {'pattern' => '/Stage[main]/Nova::Vncproxy/Nova::Generic_service[vncproxy]/Package'\
                             '[nova-vncproxy]/ensure) created', 'progress' => 0.6},
               {'pattern' => '/Stage[main]/Nova::Keystone::Auth/Keystone_service[nova_volume]/ensure) created', 'progress' => 0.68},
               {'pattern' => '/Stage[main]/Nova::Keystone::Auth/Keystone_user_role[nova@services]/ensure) created', 'progress' => 0.75},
               {'pattern' => '/Stage[main]/Nova/Exec[post-nova_config]/returns) Nova config has changed', 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Nova::Api/Exec[nova-db-sync]/returns) executed successfully', 'progress' => 0.85},
               {'pattern' => "/Stage[main]/Nova::Consoleauth/Nova::Generic_service[consoleauth]/Service"\
                             "[nova-consoleauth]/ensure) ensure changed 'stopped' to 'running'", 'progress' => 0.9},
               {'pattern' => '/Stage[main]/Nova::Network/Nova::Manage::Network[nova-vm-net]/Nova_network'\
                             'nova-vm-net]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Openstack', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Openstack::Firewall/File[iptables]/ensure) defined content as', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Openstack::Glance/Package[swift]/ensure) created', 'progress' => 0.15},
               {'pattern' => '/Stage[main]/Openstack::Auth_file/File[/root/openrc]/ensure) defined content as', 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Openstack::Controller/Nova_config[DEFAULT/memcached_servers]/ensure) created', 'progress' => 0.45},
               {'pattern' => '/Stage[main]/Openstack::Nova::Controller/Nova_config[DEFAULT/multi_host]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Openstack::Firewall/Exec[startup-firewall]/returns) executed successfully', 'progress' => 0.65},
               {'pattern' => '/Stage[main]/Openstack::Img::Cirros/Package[cirros-testvm]/ensure) created', 'progress' => 1},
               ]
            },
            ]
          },

        'puppet-log-components-list-multinode_compute-compute' =>
          {'type' => 'components-list',
          'endlog_patterns' => [{'pattern' => /Finished catalog run in [0-9]+\.[0-9]* seconds\n/, 'progress' => 1.0}],
          'chunk_size' => 40000,
          'filename' => 'puppet-agent.log',
          'components_list' => [
            {'name' => 'Keystone', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Keystone::Python/Package[python-keystone]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Mysql', 'weight' => 10, 'patterns' => [
               {'pattern' => '/Stage[main]/Mysql::Python/Package[python-mysqldb]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Nova', 'weight' => 5, 'patterns' => [
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[euca2ools]/ensure) created', 'progress' => 0.1},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[parted]/ensure) created', 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Nova::Api/Nova::Generic_service[api]/Package[nova-api]/ensure) created', 'progress' => 0.28},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[unzip]/ensure) created', 'progress' => 0.32},
               {'pattern' => '/Stage[main]/Nova::Vncproxy/Package[python-numpy]/ensure) created', 'progress' => 0.35},
               {'pattern' => '/Stage[main]/Nova::Utilities/Package[libguestfs-tools-c]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Nova::Rabbitmq/Rabbitmq_user_permissions[nova@/]/ensure) created', 'progress' => 0.43},
               {'pattern' => '/Stage[main]/Nova/Exec[post-nova_config]/returns) Nova config has changed', 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Nova::Api/Exec[nova-db-sync]/returns) executed successfully', 'progress' => 0.85},
               {'pattern' => '/Stage[main]/Nova::Network/Nova::Manage::Network[nova-vm-net]/Nova_network'\
                             'nova-vm-net]/ensure) created', 'progress' => 1},
               ]
            },
            {'name' => 'Nova::Compute', 'weight' => 15, 'patterns' => [
               {'pattern' => '/Stage[main]/Nova::Compute/Package[bridge-utils]/ensure) created', 'progress' => 0.15},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Exec[symlink-qemu-kvm]/returns) executed successfully', 'progress' => 0.25},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Package[libvirt]/ensure) created', 'progress' => 0.3},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Package[dnsmasq-utils]/ensure) created', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Nova_config[DEFAULT/vncserver_listen]/ensure) created', 'progress' => 0.55},
               {'pattern' => '/Stage[main]/Nova::Compute/Nova::Generic_service[compute]/Package[nova-compute]/ensure) created', 'progress' => 0.88},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Package[avahi]/ensure) created', 'progress' => 0.9},
               {'pattern' => '/Stage[main]/Nova::Compute::Libvirt/Service[messagebus]/ensure) ensure changed', 'progress' => 0.93},
               {'pattern' => '/Stage[main]/Nova::Compute/Nova::Generic_service[compute]/Service[nova-compute]/ensure) ensure changed', 'progress' => 0.97},
               {'pattern' => '/Stage[main]/Nova::Compute/Nova::Generic_service[compute]/Service[nova-compute]) Triggered', 'progress' => 1},
               ]
            },
            {'name' => 'Openstack', 'weight' => 2, 'patterns' => [
               {'pattern' => '/Stage[main]/Openstack::Compute/Nova_config[DEFAULT/metadata_host]/ensure) created', 'progress' => 0.2},
               {'pattern' => '/Stage[main]/Openstack::Compute/Nova_config[DEFAULT/memcached_servers]/ensure) created', 'progress' => 0.4},
               {'pattern' => '/Stage[main]/Openstack::Compute/Augeas[sysconfig-libvirt]/returns) executed successfully', 'progress' => 0.5},
               {'pattern' => '/Stage[main]/Openstack::Compute/Nova_config[DEFAULT/multi_host]/ensure) created', 'progress' => 0.8},
               {'pattern' => '/Stage[main]/Openstack::Compute/Augeas[libvirt-conf]/returns) executed successfully', 'progress' => 1},
               ]
            },
            ]
          },
        }
    end
	end
end