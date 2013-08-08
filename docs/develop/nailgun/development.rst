Nailgun Development Instructions
================================

Prepare environment
-------------------

All our development is commonly done on Ubuntu 12. Follow the steps to prepare an environment:

#. Install and configure Postgres DB::

    sudo apt-get install postgresql
    sudo -u postgres createuser -D -A -P nailgun (enter password nailgun)
    sudo -u postgres createdb nailgun
    sudo apt-get install postgresql-server-dev-9.1 python-dev
    sudo pip install psycopg2

#. Install python dependencies (cobbler can't be installed from pypi)::

    sudo pip install -r requirements-eggs.txt
    sudo pip install PyYAML
    git clone git://github.com/cobbler/cobbler.git
    cd cobbler
    git checkout release24
    sudo make install

#. SyncDB::

    cd nailgun
    ./manage.py syncdb
    ./manage.py loaddefault # It loads all basic fixtures listed in settings.yaml, such as admin_network, startup_notification and so on
    ./manage.py loaddata nailgun/fixtures/sample_environment.json  # Loads fake nodes

#. Create required folder for log files::

    sudo mkdir /var/log/nailgun
    sudo chown -R `whoami`.`whoami` /var/log/nailgun

#. Start application in "fake" mode, when no real calls to orchestrator are performed::

    python manage.py run -p 8000 --fake-tasks | grep --line-buffered -v -e HTTP -e '^$' >> /var/log/nailgun.log 2>&1 &

#. (optional) You can also use --fake-tasks-amqp option if you want to make fake environment use real RabbitMQ instead of fake one::

    python manage.py run -p 8000 --fake-tasks-amqp | grep --line-buffered -v -e HTTP -e '^$' >> /var/log/nailgun.log 2>&1 &

How to add new volume on node
-----------------------------

1. Add data into release metadata file (nailgun/fixtures/openstack.json or nailgun/fixtures/redhat.json):
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

There are two possible ways to add new volume to slave node. The first way is to add new logical volume definition into one of the existant volumes groups, let say 'os' volume group::

  {
    "id": "os",
    "type": "vg",
    "min_size": {"generator": "calc_min_os_size"},
    "label": "Base System",
    "volumes": [
        {
            "mount": "/",
            "type": "lv",
            "name": "root",
            "size": {"generator": "calc_total_root_vg"}
        },
        {
            "mount": "swap",
            "type": "lv",
            "name": "swap",
            "size": {"generator": "calc_swap_size"}
        },
        {
            "mount": "/mnt/some/path",
            "type": "lv",
            "name": "LOGICAL_VOLUME_NAME",
            "size": {
                "generator": "calc_LOGICAL_VOLUME_size",
                "generator_args": ["arg1", "arg2"]
            }
        }
    ]
  }

Here *id* is the volume group name. It is important that the name of the logical volume must not be the same as the volume group name. The field *size* in the logical volume definition can be defined directly as the integer number in megabytes or it can be defined indirectly via so called generator. Generator is just the python lambda that can be called to calculate logical volume size dynamically. Here in the json definition size is defined as the dictionary with two keys: 'generator' is the name of the generator and 'generator_args' is the list of arguments which will be passed to generator lambda.

The second way to add new volume to slave nodes is to create new volume group and to define logical volume (one or more) inside the volume group definition::

    {
        "id": "NEW_VOLUME_GROUP_NAME",
        "type": "vg",
        "min_size": {"generator": "calc_NEW_VOLUME_NAME_size"},
        "label": "Label for NEW VOLUME GROUP as it will be shown on UI",
        "volumes": [
            {
                "mount": "/path/to/mount/point",
                "type": "lv",
                "name": "LOGICAL_VOLUME_NAME",
                "size": {
                    "generator": "another_generator_to_calc_LOGICAL_VOLUME_size",
                    "generator_args": ["arg"]
                }
            }
        ]
    }

Besides it is possible to define sizes or whatever you want in the nailgun configuration file (/etc/nailgun/settings.yaml). All fixture files are templated just before being loaded into nailgun database. We use jinja2 templating engine. For example, we can define new logical volume mount point as follows::

    "mount": "{{settings.NEW_LOGICAL_VOLUME_MOUNT_POINT}}"

Of course *NEW_LOGICAL_VOLUME_MOUNT_POINT* must be defined in settings file.

If we add new volume group then we need to map it on the node roles. To make new volume group active we just need to add its name to the list of volume groups for a given role (the same file where volume groups are defined)::

    {
        "volumes_roles_mapping": {
            "controller": ["os", "image"],
            "compute": ["os", "vm", "VOLUME_GROUP_NAME"],
            "cinder": ["os", "cinder"]
        }
    }


2. Add generators into nailgun/volumes/manager.py
+++++++++++++++++++++++++++++++++++++++++++++++++

There is the method in the VolumeManager class where generators are defined. New volume generator 'NEW_GENERATOR_TO_CALCULATE_SIZ' needs to be added in the generators dictionary inside this method.

.. code-block:: python

    class VolumeManager(object):
        ...
        def call_generator(self, generator, *args):
            generators = {
                ...
                'NEW_GENERATOR_TO_CALCULATE_SIZE': lambda: 1000,
                ...
            }

3. That is it.
++++++++++++++

Nailgun will add new volume for a given role in its GET responses to /api/nodes/<id>/volumes. It also will add new volume in ks_spaces variable which is used by cobbler to create kickstart partition commands. We do not need to add anything else except we want to have something special. For example, at the moment we do not have the possibility to define file system type for logical volumes. And if it is needed to be hard coded somewhere it could be done inside cobbler snippet fuel/deployment/puppet/cobbler/templates/snippets/pre_install_partition_lvm.erb
