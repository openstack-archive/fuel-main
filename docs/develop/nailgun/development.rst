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

1. Add new volume into release metadata (nailgun/fixtures/openstack.json):

Volume format is as follows::

    {
        "id": "VOLUME_GROUP_NAME",
        "type": "vg",
        "min_size": {"generator": "calc_min_VOLUME_NAME_size"},
        "label": "Label how it will be shown on UI",
        "volumes": [
            {
                "mount": "/path/to/mount/point",
                "type": "lv",
                "name": "VOLUME_NAME",
                "size": {
                    "generator": "calc_total_vg",
                    "generator_args": ["VOLUME_GROUP_NAME"]
                }
            }
        ]
    }

Do not forget to map new volume into the node roles::

    {
        "volumes_roles_mapping": {
            "controller": ["os", "image"],
            "compute": ["os", "vm", "VOLUME_GROUP_NAME"],
            "cinder": ["os", "cinder"]
        }
    }


2. Add generators into nailgun/volumes/manager.py

There is the method in the VolumeManager class where volume calculators are defined. New volume generator 'calc_min_VOLUME_NAME_size' needs to be added in the generators dictionary.

.. code-block:: python

    def call_generator(self, generator, *args):
        generators = {
            ...
            'calc_min_VOLUME_NAME_size': lambda: gb_to_mb(10),
            ...
        }

3. That is it. Nailgun will add new volume for a given role in the its GET responses to /api/nodes/<id>/volumes. It also will add new volume in ks_spaces variable which is used by cobbler to create kickstart partition commands.
