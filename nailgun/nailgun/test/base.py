# -*- coding: utf-8 -*-

try:
    from unittest.case import TestCase
except ImportError:
    # Runing unit-tests in production environment
    from unittest2.case import TestCase

import os
import re
import json
import time
import logging
import mock
from random import randint
from datetime import datetime
from functools import partial, wraps
from paste.fixture import TestApp, AppError

import nailgun
from nailgun.api.models import Node
from nailgun.api.models import Release
from nailgun.api.models import Cluster
from nailgun.api.models import Notification
from nailgun.api.models import Attributes
from nailgun.api.models import Network
from nailgun.api.models import NetworkGroup
from nailgun.api.models import Task
from nailgun.api.urls import urls
from nailgun.wsgi import build_app
from nailgun.db import engine
from nailgun.db import dropdb, syncdb, flush, orm
from nailgun.fixtures.fixman import upload_fixture
from nailgun.network.manager import NetworkManager


class TimeoutError(Exception):
    pass


class Environment(object):

    def __init__(self, app, db=None):
        self.db = db or orm()
        self.app = app
        self.tester = TestCase
        self.tester.runTest = lambda a: None
        self.tester = self.tester()
        self.here = os.path.abspath(os.path.dirname(__file__))
        self.fixture_dir = os.path.join(self.here, "..", "fixtures")
        self.default_headers = {
            "Content-Type": "application/json"
        }
        self.releases = []
        self.clusters = []
        self.nodes = []
        self.network_manager = NetworkManager(db=self.db)

    def create(self, **kwargs):
        cluster = self.create_cluster(
            **kwargs.pop('cluster_kwargs', {})
        )
        for node_kwargs in kwargs.pop('nodes_kwargs', []):
            if "cluster_id" not in node_kwargs:
                if isinstance(cluster, dict):
                    node_kwargs["cluster_id"] = cluster["id"]
                else:
                    node_kwargs["cluster_id"] = cluster.id
            node_kwargs.setdefault("api", False)
            self.create_node(
                **node_kwargs
            )

    def create_release(self, api=False, **kwargs):
        version = str(randint(0, 100000000))
        release_data = {
            'name': u"release_name_" + version,
            'version': version,
            'description': u"release_desc" + version,
            'networks_metadata': self.get_default_networks_metadata(),
            'attributes_metadata': self.get_default_attributes_metadata(),
            'volumes_metadata': self.get_default_volumes_metadata()
        }
        if kwargs:
            release_data.update(kwargs)
        if api:
            resp = self.app.post(
                reverse('ReleaseCollectionHandler'),
                params=json.dumps(release_data),
                headers=self.default_headers
            )
            self.tester.assertEquals(resp.status, 201)
            release = json.loads(resp.body)
            self.releases.append(
                self.db.query(Release).get(release['id'])
            )
        else:
            release = Release()
            for field, value in release_data.iteritems():
                setattr(release, field, value)
            self.db.add(release)
            self.db.commit()
            self.releases.append(release)
        return release

    def create_cluster(self, api=True, exclude=None, **kwargs):
        cluster_data = {
            'name': 'cluster-api-' + str(randint(0, 1000000))
        }
        if kwargs:
            cluster_data.update(kwargs)
        if api:
            cluster_data['release'] = self.create_release(api=False).id
        else:
            cluster_data['release'] = self.create_release(api=False)
        if exclude and isinstance(exclude, list):
            for ex in exclude:
                try:
                    del cluster_data[ex]
                except KeyError as err:
                    logging.warning(err)
        if api:
            resp = self.app.post(
                reverse('ClusterCollectionHandler'),
                json.dumps(cluster_data),
                headers=self.default_headers
            )
            self.tester.assertEquals(resp.status, 201)
            cluster = json.loads(resp.body)
            self.clusters.append(
                self.db.query(Cluster).get(cluster['id'])
            )
        else:
            cluster = Cluster()
            for field, value in cluster_data.iteritems():
                setattr(cluster, field, value)
            self.db.add(cluster)
            self.db.commit()
            self.clusters.append(cluster)
        return cluster

    def create_node(
            self, api=False,
            exclude=None, expect_http=201,
            expect_message=None,
            **kwargs):
        node_data = {
            'mac': self._generate_random_mac(),
            'role': 'controller',
            'status': 'discover',
            'meta': self.default_metadata()
        }
        if kwargs:
            node_data.update(kwargs)
        if exclude and isinstance(exclude, list):
            for ex in exclude:
                try:
                    del node_data[ex]
                except KeyError as err:
                    logging.warning(err)
        if api:
            resp = self.app.post(
                reverse('NodeCollectionHandler'),
                json.dumps(node_data),
                headers=self.default_headers,
                expect_errors=True
            )
            self.tester.assertEquals(resp.status, expect_http)
            if expect_message:
                self.tester.assertEquals(resp.body, expect_message)
            if str(expect_http)[0] != "2":
                return None
            self.tester.assertEquals(resp.status, expect_http)
            node = json.loads(resp.body)
            self.nodes.append(
                self.db.query(Node).get(node['id'])
            )
        else:
            node = Node()
            node.timestamp = datetime.now()
            for key, value in node_data.iteritems():
                setattr(node, key, value)
            self.db.add(node)
            self.db.commit()
            self.nodes.append(node)
        return node

    def create_notification(self, **kwargs):
        notif_data = {
            "topic": "discover",
            "message": "Test message",
            "status": "unread",
            "datetime": datetime.now()
        }
        if kwargs:
            notif_data.update(kwargs)
        notification = Notification()
        notification.cluster_id = notif_data.get("cluster_id")
        for f, v in notif_data.iteritems():
            setattr(notification, f, v)
        self.db.add(notification)
        self.db.commit()
        return notification

    def default_metadata(self):
        item = self.find_item_by_pk_model(
            self.read_fixtures(("sample_environment",)),
            1, 'nailgun.node')
        return item.get('fields').get('meta')

    def _generate_random_mac(self):
        mac = [randint(0x00, 0x7f) for _ in xrange(6)]
        return ':'.join(map(lambda x: "%02x" % x, mac)).upper()

    def generate_interfaces_in_meta(self, amount):
        nics = []
        for i in xrange(amount):
            nics.append(
                {
                    'name': 'eth{0}'.format(i),
                    'mac': self._generate_random_mac(),
                    'current_speed': 100,
                    'max_speed': 1000
                }
            )
        return {'interfaces': nics}

    def generate_ui_networks(self, cluster_id):
        start_id = self.db.query(NetworkGroup.id).order_by(
            NetworkGroup.id
        ).first()
        start_id = 0 if not start_id else start_id[-1] + 1
        net_names = (
            "floating_test",
            "public_test",
            "management_test",
            "storage_test",
            "fixed_test"
        )
        net_cidrs = (
            "240.0.0.0/24",
            "240.0.1.0/24",
            "192.168.0.0/24",
            "172.16.0.0/24",
            "10.0.0.0/24"
        )
        nets = {'networks': [{
            "network_size": 256,
            "name": nd[0],
            "amount": 1,
            "cluster_id": cluster_id,
            "vlan_start": 100 + i,
            "cidr": nd[1],
            "id": start_id + i
        } for i, nd in enumerate(zip(net_names, net_cidrs))]}
        return nets

    def get_default_volumes_metadata(self):
        return {
            "controller": [
                {
                    "type": "vg",
                    "id": "os",
                    "volumes": [
                        {
                            "mount": "/",
                            "type": "lv",
                            "name": "root",
                            "size": {"generator": "calc_root_size"}
                        },
                        {
                            "mount": "swap",
                            "type": "lv",
                            "name": "swap",
                            "size": {"generator": "calc_swap_size"}
                        }
                    ]
                },
                {
                    "type": "vg",
                    "id": "cinder",
                    "volumes": []
                }
            ],
            "compute": [
                {
                    "type": "vg",
                    "id": "os",
                    "volumes": [
                        {
                            "mount": "/",
                            "type": "lv",
                            "name": "root",
                            "size": {"generator": "calc_root_size"}
                        },
                        {
                            "mount": "swap",
                            "type": "lv",
                            "name": "swap",
                            "size": {"generator": "calc_swap_size"}
                        }
                    ]
                },
                {
                    "type": "vg",
                    "id": "vm",
                    "volumes": [
                        {
                            "mount": "/var/lib/libvirt",
                            "type": "lv",
                            "name": "vm",
                            "size": {"generator": "calc_all_free"}
                        }
                    ]
                },
                {
                    "type": "vg",
                    "id": "cinder",
                    "volumes": []
                }
            ],
            "cinder": [
                {
                    "type": "vg",
                    "id": "os",
                    "volumes": [
                        {
                            "mount": "/",
                            "type": "lv",
                            "name": "root",
                            "size": {"generator": "calc_root_size"}
                        },
                        {
                            "mount": "swap",
                            "type": "lv",
                            "name": "swap",
                            "size": {"generator": "calc_swap_size"}
                        }
                    ]
                },
                {
                    "type": "vg",
                    "id": "cinder",
                    "volumes": []
                }
            ]
        }

    def get_default_networks_metadata(self):
        return [
            {"name": "floating", "access": "public"},
            {"name": "fixed", "access": "private10"},
            {"name": "storage", "access": "private192"},
            {"name": "management", "access": "private172"},
            {"name": "public", "access": "public"}
        ]

    def get_default_attributes_metadata(self):
        return {
            "editable": {
                "admin_tenant": {
                    "value": "admin",
                    "label": "Admin tenant",
                    "description": "Tenant(project) name for Administrator"
                },
                "common": {
                    "auto_assign_floating_ip": {
                        "value": False,
                        "label": "Auto assign floating IP",
                        "description": "Description"
                    },
                    "libvirt_type": {
                        "value": "kvm",
                        "values": [
                            {
                                "data": "kvm",
                                "display_name": "KVM",
                                "description": "Choose this type..."
                            },
                            {
                                "data": "qemu",
                                "display_name": "QEMU",
                                "description": "Choose this type..."
                            }
                        ],
                        "label": "Hypervisor type"
                    },
                }
            },
            "generated": {
                "mysql": {
                    "root_password": {
                        "generator": "password"
                    },
                    "predefined": {
                        "generator": "identical",
                        "generator_args": "i am value"
                    }
                },
                "keystone": {
                    "token": {
                        "generator": "password"
                    }
                }
            }
        }

    def upload_fixtures(self, fxtr_names):
        for fxtr_path in self.fxtr_paths_by_names(fxtr_names):
            with open(fxtr_path, "r") as fxtr_file:
                upload_fixture(fxtr_file)

    def read_fixtures(self, fxtr_names):
        data = []
        for fxtr_path in self.fxtr_paths_by_names(fxtr_names):
            with open(fxtr_path, "r") as fxtr_file:
                try:
                    data.extend(json.load(fxtr_file))
                except:
                    logging.error(
                        "Error occurred while loading "
                        "fixture %s" % fxtr_path
                    )
        return data

    def fxtr_paths_by_names(self, fxtr_names):
        for fxtr in fxtr_names:
            fxtr_path = os.path.join(
                self.fixture_dir,
                "%s.json" % fxtr
            )

            if not os.path.exists(fxtr_path):
                logging.warning(
                    "Fixture file was not found: %s",
                    fxtr_path
                )
                break
            else:
                logging.debug(
                    "Fixture file is found, yielding path: %s",
                    fxtr_path
                )
                yield fxtr_path

    def find_item_by_pk_model(self, data, pk, model):
        for item in data:
            if item.get('pk') == pk and item.get('model') == model:
                return item

    def launch_deployment(self):
        if self.clusters:
            resp = self.app.put(
                reverse(
                    'ClusterChangesHandler',
                    kwargs={'cluster_id': self.clusters[0].id}),
                headers=self.default_headers
            )
            self.tester.assertEquals(200, resp.status)
            response = json.loads(resp.body)
            return self.db.query(Task).filter_by(
                uuid=response['uuid']
            ).first()
        else:
            raise NotImplementedError(
                "Nothing to deploy - try creating cluster"
            )

    def launch_verify_networks(self, data=None):
        if self.clusters:
            if data:
                nets = json.dumps(data)
            else:
                resp = self.app.get(
                    reverse(
                        'NetworkConfigurationHandler',
                        kwargs={'cluster_id': self.clusters[0].id}
                    ),
                    headers=self.default_headers
                )
                self.tester.assertEquals(200, resp.status)
                nets = resp.body

            resp = self.app.put(
                reverse(
                    'NetworkConfigurationVerifyHandler',
                    kwargs={'cluster_id': self.clusters[0].id}),
                nets,
                headers=self.default_headers
            )
            self.tester.assertEquals(200, resp.status)
            response = json.loads(resp.body)
            task_uuid = response['uuid']
            return self.db.query(Task).filter_by(uuid=task_uuid).first()
        else:
            raise NotImplementedError(
                "Nothing to verify - try creating cluster"
            )

    def refresh_nodes(self):
        for i, n in enumerate(self.nodes[:]):
            try:
                self.db.refresh(n)
            except:
                del self.nodes[i]

    def refresh_clusters(self):
        for i, n in enumerate(self.clusters[:]):
            try:
                self.db.refresh(n)
            except:
                del self.clusters[i]

    def _wait_task(self, task, timeout, message):
        timer = time.time()
        while task.status == 'running':
            self.db.refresh(task)

            if time.time() - timer > timeout:
                raise Exception(
                    "Task '{0}' seems to be hanged".format(
                        task.name
                    )
                )
            time.sleep(1)
        self.tester.assertEquals(task.progress, 100)
        if isinstance(message, type(re.compile("regexp"))):
            self.tester.assertIsNotNone(re.match(message, task.message))
        elif isinstance(message, str):
            self.tester.assertEquals(task.message, message)

    def wait_ready(self, task, timeout=60, message=None):
        self._wait_task(task, timeout, message)
        self.tester.assertEquals(task.status, 'ready')

    def wait_error(self, task, timeout=60, message=None):
        self._wait_task(task, timeout, message)
        self.tester.assertEquals(task.status, 'error')

    def wait_for_nodes_status(self, nodes, status):
        def check_statuses():
            self.refresh_nodes()

            nodes_with_status = filter(
                lambda x: x.status in status,
                nodes)

            return len(nodes) == len(nodes_with_status)

        self._wait_for_success(
            check_statuses,
            error_message='Something wrong with the statuses')

    def _wait_for_success(self, func, args=[], kwargs={},
                          seconds=10, error_message='Timeout error'):

        start_time = time.time()

        while True:
            result = func(*args, **kwargs)
            if result:
                return result
            if time.time() - start_time > seconds:
                raise TimeoutError(error_message)
            time.sleep(0.1)


class BaseHandlers(TestCase):

    fixtures = ["admin_network"]

    def __init__(self, *args, **kwargs):
        super(BaseHandlers, self).__init__(*args, **kwargs)
        self.mock = mock
        self.default_headers = {
            "Content-Type": "application/json"
        }

    def _wait_for_threads(self):
        # wait for fake task thread termination
        import threading
        for thread in threading.enumerate():
            if thread is not threading.currentThread():
                if hasattr(thread, "rude_join"):
                    timer = time.time()
                    timeout = 25
                    thread.rude_join(timeout)
                    if time.time() - timer > timeout:
                        raise Exception(
                            '{0} seconds is not enough'
                            ' - possible hanging'.format(
                                timeout
                            )
                        )

    @classmethod
    def setUpClass(cls):
        cls.db = orm()
        cls.app = TestApp(build_app().wsgifunc())
        nailgun.task.task.DeploymentTask._prepare_syslog_dir = mock.Mock()
        #dropdb()
        syncdb()

    @classmethod
    def tearDownClass(cls):
        flush()
        cls.db.commit()
        cls.db.close()

    def setUp(self):
        self.default_headers = {
            "Content-Type": "application/json"
        }
        flush()
        self.env = Environment(app=self.app, db=self.db)
        # hack for admin net
        map(
            self.db.delete,
            self.db.query(Network).all(),
        )
        self.db.commit()
        self.env.upload_fixtures(self.fixtures)


def fake_tasks(fake_rpc=True, **kwargs):
    def wrapper(func):
        func = mock.patch(
            'nailgun.task.task.settings.FAKE_TASKS',
            True
        )(func)
        func = mock.patch(
            'nailgun.task.fake.settings.FAKE_TASKS_TICK_COUNT',
            99
        )(func)
        func = mock.patch(
            'nailgun.task.fake.settings.FAKE_TASKS_TICK_INTERVAL',
            1
        )(func)
        if fake_rpc and not kwargs:
            func = mock.patch(
                'nailgun.task.task.rpc.cast',
                nailgun.task.task.fake_cast
            )(func)
        elif fake_rpc and kwargs:
            func = mock.patch(
                'nailgun.task.task.rpc.cast',
                partial(
                    nailgun.task.task.fake_cast,
                    **kwargs
                )
            )(func)
        else:
            func = mock.patch(
                'nailgun.task.task.rpc.cast'
            )(func)
        return func
    return wrapper


def reverse(name, kwargs=None):
    urldict = dict(zip(urls[1::2], urls[::2]))
    url = urldict[name]
    urlregex = re.compile(url)
    for kwarg in urlregex.groupindex:
        if not kwarg in kwargs:
            raise KeyError("Invalid argument specified")
        url = re.sub(
            r"\(\?P<{0}>[^)]+\)".format(kwarg),
            str(kwargs[kwarg]),
            url,
            1
        )
    url = re.sub(r"\??\$", "", url)
    return "/api" + url
