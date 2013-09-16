# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

try:
    from unittest.case import TestCase
except ImportError:
    # Runing unit-tests in production environment
    from unittest2.case import TestCase

from datetime import datetime
from functools import partial
from itertools import izip
import json
import logging
import mock
import os
from random import randint
import re
import time

from paste.fixture import TestApp

import nailgun
from nailgun.api.models import Cluster
from nailgun.api.models import NetworkGroup
from nailgun.api.models import Node
from nailgun.api.models import NodeAttributes
from nailgun.api.models import NodeNICInterface
from nailgun.api.models import Notification
from nailgun.api.models import Release
from nailgun.api.models import Task
from nailgun.api.urls import urls
from nailgun.db import db
from nailgun.db import flush
from nailgun.db import syncdb
from nailgun.fixtures.fixman import upload_fixture
from nailgun.network.manager import NetworkManager
from nailgun.wsgi import build_app


class TimeoutError(Exception):
    pass


class Environment(object):

    def __init__(self, app):
        self.db = db()
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
        self.network_manager = NetworkManager()

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
        return cluster

    def create_release(self, api=False, **kwargs):
        version = str(randint(0, 100000000))
        release_data = {
            'name': u"release_name_" + version,
            'version': version,
            'description': u"release_desc" + version,
            'operating_system': 'CensOS',
            'roles': self.get_default_roles(),
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

    def download_release(self, release_id):
        release_data = {
            'license_type': 'rhsm',
            'username': 'rheltest',
            'password': 'password',
            'release_id': release_id
        }

        resp = self.app.post(
            reverse('RedHatAccountHandler'),
            params=json.dumps(release_data),
            headers=self.default_headers
        )
        self.tester.assertEquals(resp.status, 200)
        download_task = json.loads(resp.body)
        return self.db.query(Task).get(download_task['id'])

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
        metadata = kwargs.get('meta')
        default_metadata = self.default_metadata()
        if metadata:
            default_metadata.update(metadata)

        mac = self._generate_random_mac()
        if default_metadata['interfaces']:
            default_metadata['interfaces'][0]['mac'] = kwargs.get('mac', mac)

        node_data = {
            'mac': mac,
            'roles': ['controller'],
            'status': 'discover',
            'meta': default_metadata
        }
        if kwargs:
            meta = kwargs.pop('meta', None)
            node_data.update(kwargs)
            if meta:
                kwargs['meta'] = meta

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
            node_db = self.db.query(Node).get(node['id'])
            self._set_interfaces_if_not_set_in_meta(
                node_db.id,
                kwargs.get('meta', None))
            self.nodes.append(node_db)
        else:
            node = Node()
            node.timestamp = datetime.now()
            if 'cluster_id' in node_data:
                cluster_id = node_data.pop('cluster_id')
                for cluster in self.clusters:
                    if cluster.id == cluster_id:
                        node.cluster = cluster
                        break
                else:
                    node.cluster_id = cluster_id
            for key, value in node_data.iteritems():
                setattr(node, key, value)
            node.attributes = self.create_attributes()
            node.attributes.volumes = node.volume_manager.gen_volumes_info()
            self.db.add(node)
            self.db.commit()
            self._set_interfaces_if_not_set_in_meta(
                node.id,
                kwargs.get('meta', None))

            self.nodes.append(node)

        return node

    def create_attributes(self):
        return NodeAttributes()

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

    def _set_interfaces_if_not_set_in_meta(self, node_id, meta):
        if not meta or not 'interfaces' in meta:
            self._add_interfaces_to_node(node_id)

    def _add_interfaces_to_node(self, node_id, count=1):
        interfaces = []
        allowed_networks = list(self.db.query(NetworkGroup).filter(
            NetworkGroup.id.in_(
                self.network_manager.get_all_cluster_networkgroups(node_id)
            )
        ))

        for i in xrange(count):
            nic_dict = {
                'node_id': node_id,
                'name': 'eth{0}'.format(i),
                'mac': self._generate_random_mac(),
                'current_speed': 100,
                'max_speed': 1000,
                'allowed_networks': allowed_networks,
                'assigned_networks': allowed_networks
            }

            interface = NodeNICInterface()
            for k, v in nic_dict.iteritems():
                setattr(interface, k, v)

            self.db.add(interface)
            self.db.commit()

            interfaces.append(interface)

        return interfaces

    def generate_ui_networks(self, cluster_id):
        start_id = self.db.query(NetworkGroup.id).order_by(
            NetworkGroup.id
        ).first()
        start_id = 0 if not start_id else start_id[-1] + 1
        net_names = (
            "floating",
            "public",
            "management",
            "storage",
            "fixed"
        )
        net_cidrs = (
            "172.16.0.0/24",
            "172.16.1.0/24",
            "192.168.0.0/24",
            "192.168.0.0/24",
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

        public = filter(
            lambda net: net['name'] == 'public',
            nets['networks'])[0]
        public['netmask'] = '255.255.255.0'

        return nets

    def get_default_roles(self):
        return ['controller', 'compute', 'cinder', 'ceph-osd']

    def get_default_volumes_metadata(self):
        return self.read_fixtures(
            ('openstack',))[0]['fields']['volumes_metadata']

    def get_default_networks_metadata(self):
        return [
            {"name": "floating", "access": "public"},
            {"name": "public", "access": "public"},
            {"name": "management", "access": "private192"},
            {"name": "storage", "access": "private192"},
            {"name": "fixed", "access": "private10"}
        ]

    def get_default_attributes_metadata(self):
        return self.read_fixtures(
            ['openstack'])[0]['fields']['attributes_metadata']

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
                except Exception as exc:
                    logging.error(
                        'Error "%s" occurred while loading '
                        'fixture %s' % (exc, fxtr_path)
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
                headers=self.default_headers)
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
        for n in self.nodes[:]:
            try:
                self.db.add(n)
                self.db.refresh(n)
            except Exception:
                self.nodes.remove(n)

    def refresh_clusters(self):
        for n in self.clusters[:]:
            try:
                self.db.refresh(n)
            except Exception:
                self.nodes.remove(n)

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

        self.wait_for_true(
            check_statuses,
            error_message='Something wrong with the statuses')

    def wait_for_true(self, check, args=[], kwargs={},
                      timeout=60, error_message='Timeout error'):

        start_time = time.time()

        while True:
            result = check(*args, **kwargs)
            if result:
                return result
            if time.time() - start_time > timeout:
                raise TimeoutError(error_message)
            time.sleep(0.1)


class BaseTestCase(TestCase):
    fixtures = ['admin_network']

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
        self.default_headers = {
            "Content-Type": "application/json"
        }

    @classmethod
    def setUpClass(cls):
        cls.db = db()
        cls.app = TestApp(build_app().wsgifunc())
        syncdb()

    @classmethod
    def tearDownClass(cls):
        cls.db.commit()

    def setUp(self):
        flush()
        self.env = Environment(app=self.app)
        self.env.upload_fixtures(self.fixtures)

    def tearDown(self):
        self.db.expunge_all()

    def assertNotRaises(self, exception, method, *args, **kwargs):
        try:
            method(*args, **kwargs)
        except exception:
            self.fail('Exception "{0}" raised.'.format(exception))

    def datadiff(self, node1, node2, path=None):
        if path is None:
            path = []

        print("Path: {0}".format("->".join(path)))

        if not isinstance(node1, dict) or not isinstance(node2, dict):
            if isinstance(node1, list):
                newpath = path[:]
                for i, keys in enumerate(izip(node1, node2)):
                    newpath.append(str(i))
                    self.datadiff(keys[0], keys[1], newpath)
                    newpath.pop()
            elif node1 != node2:
                err = "Values differ: {0} != {1}".format(
                    str(node1),
                    str(node2)
                )
                raise Exception(err)
        else:
            newpath = path[:]
            for key1, key2 in zip(
                sorted(node1.keys()),
                sorted(node2.keys())
            ):
                if key1 != key2:
                    err = "Keys differ: {0} != {1}".format(
                        str(key1),
                        str(key2)
                    )
                    raise Exception(err)
                newpath.append(key1)
                self.datadiff(node1[key1], node2[key2], newpath)
                newpath.pop()


class BaseIntegrationTest(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super(BaseIntegrationTest, cls).setUpClass()
        nailgun.task.task.DeploymentTask._prepare_syslog_dir = mock.Mock()

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


def fake_tasks(fake_rpc=True,
               mock_rpc=True,
               **kwargs):
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
        elif mock_rpc:
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
        if kwarg not in kwargs:
            raise KeyError("Invalid argument specified")
        url = re.sub(
            r"\(\?P<{0}>[^)]+\)".format(kwarg),
            str(kwargs[kwarg]),
            url,
            1
        )
    url = re.sub(r"\??\$", "", url)
    return "/api" + url


# this method is for development and troubleshooting purposes
def datadiff(data1, data2, branch, p=True):
    def iterator(data1, data2):
        if isinstance(data1, (list,)) and isinstance(data2, (list,)):
            return xrange(max(len(data1), len(data2)))
        elif isinstance(data1, (dict,)) and isinstance(data2, (dict,)):
            return (set(data1.keys()) | set(data2.keys()))
        else:
            raise TypeError

    diff = []
    if data1 != data2:
        try:
            it = iterator(data1, data2)
        except Exception:
            return [(branch, data1, data2)]

        for k in it:
            newbranch = branch[:]
            newbranch.append(k)

            if p:
                print("Comparing branch: %s" % newbranch)
            try:
                try:
                    v1 = data1[k]
                except (KeyError, IndexError):
                    if p:
                        print("data1 seems does not have key = %s" % k)
                    diff.append((newbranch, None, data2[k]))
                    continue
                try:
                    v2 = data2[k]
                except (KeyError, IndexError):
                    if p:
                        print("data2 seems does not have key = %s" % k)
                    diff.append((newbranch, data1[k], None))
                    continue

            except Exception:
                if p:
                    print("data1 and data2 cannot be compared on "
                          "branch: %s" % newbranch)
                return diff.append((newbranch, data1, data2))

            else:
                if v1 != v2:
                    if p:
                        print("data1 and data2 do not match "
                              "each other on branch: %s" % newbranch)
                        # print("data1 = %s" % data1)
                        print("v1 = %s" % v1)
                        # print("data2 = %s" % data2)
                        print("v2 = %s" % v2)
                    diff.extend(datadiff(v1, v2, newbranch))
    return diff
