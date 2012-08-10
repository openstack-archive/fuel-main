
class OpenstackCommon(object):
    mysql_port = 3306

    @classmethod
    def setUpMysql(klass, reuse_cached=True):
        if not klass.node.has_snapshot('openstack-mysql') or not reuse_cached:
            klass.upload_cookbooks(['mysql'])

            klass.chef_solo({
                'recipes': ['mysql::server'],
                'mysql': {
                    'port': klass.mysql_port,
                    'db_maker_password': 'secret'
                },
            })

            if not klass.node.has_snapshot('openstack-mysql'):
                klass.node.save_snapshot('openstack-mysql')
        else:
            klass.node.restore_snapshot('openstack-mysql')
            klass.remote.reconnect()


    keystone_admin_token = 'secret'
    keystone_admin_port  = 37376
    keystone_public_port = 5000

    @classmethod
    def setUpKeystone(klass, reuse_cached=True):
        if not klass.node.has_snapshot('openstack-keystone') or not reuse_cached:
            klass.setUpMysql()

            klass.upload_cookbooks(['chef-resource-groups', 'database', 'keystone'])

            klass.chef_solo({
                'recipes': ['keystone::server'],
                'mysql': {
                    'admin': {
                        'host': str(klass.ip),
                        'port': klass.mysql_port,
                        'username': 'db_maker',
                        'password': 'secret'
                    }
                 },
                'keystone': {
                    'db': {
                        'password': 'secret'
                    },
                    'admin_port': klass.keystone_admin_port,
                    'public_port': klass.keystone_public_port,
                    'admin_token': klass.keystone_admin_token,
                    'service_tenant': 'service',
                    'admin_tenant': 'admin',
                    'admin_user': 'admin',
                    'admin_password': 'admin',
                    'admin_role': 'admin',
                    'admin_url': 'http://%s:%s/' % (klass.ip,
                            klass.keystone_admin_port),
                    'public_url': 'http://%s:%s/' % (klass.ip,
                            klass.keystone_public_port),
                    'internal_url': 'http://%s:%s/' % (klass.ip,
                            klass.keystone_public_port),
                    'admin': {
                        'host': str(klass.ip),
                        'admin_port': klass.keystone_admin_port,
                        'service_port': klass.keystone_public_port,
                    },
                    'public': {
                        'host': str(klass.ip),
                        'admin_port': klass.keystone_admin_port,
                        'service_port': klass.keystone_public_port,
                    },
                },
            })

            if not klass.node.has_snapshot('openstack-keystone'):
                klass.node.save_snapshot('openstack-keystone')
        else:
            klass.node.restore_snapshot('openstack-keystone')
            klass.remote.reconnect()


    glance_registry_port = 9191

    @classmethod
    def setUpGlanceRegistry(klass, reuse_cached=True):
        if not klass.node.has_snapshot('openstack-glance-registry') or not reuse_cached:
            klass.setUpKeystone()

            klass.upload_cookbooks(['chef-resource-groups', 'database', 'keystone', 'glance'])

            klass.chef_solo({
                'recipes': ['glance::registry'],
                'glance': {
                    'registry': {
                        'port': klass.glance_registry_port,
                    },
                },
                'services': {
                    'glance_registry': {
                        'endpoints': {
                            'mysql': {
                                'host': str(klass.ip),
                                'port': klass.mysql_port,
                                'username': 'db_maker',
                                'password': 'secret',
                            },
                            'keystone_admin': {
                                'host': str(klass.ip),
                                'port': klass.keystone_admin_port,
                                'username': 'admin',
                                'token': 'keystone_secret',
                            },
                        }
                    },
                }
            })
            
            if not klass.node.has_snapshot('openstack-glance-registry'):
                klass.node.save_snapshot('openstack-glance-registry')
        else:
            klass.node.restore_snapshot('openstack-glance-registry')
            klass.remote.reconnect()

