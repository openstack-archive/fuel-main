# -*- coding: utf-8 -*-

import re
import json
from random import randint
from unittest.case import TestCase

import mock
from paste.fixture import TestApp
from sqlalchemy.orm.events import orm

from api.models import engine, Node, Release, Cluster, Role
from api.urls import urls
from manage import app
from db import dropdb, syncdb, flush


class BaseHandlers(TestCase):
    def __init__(self, *args, **kwargs):
        super(BaseHandlers, self).__init__(*args, **kwargs)
        self.mock = mock

    @classmethod
    def setUpClass(cls):
        dropdb()
        syncdb()

    def setUp(self):
        self.app = TestApp(app.wsgifunc())
        self.db = orm.scoped_session(orm.sessionmaker(bind=engine))()
        self.default_headers = {
            "Content-Type": "application/json"
        }
        flush()

    def default_metadata(self):
        metadata = {'block_device': 'new-val',
                    'interfaces': 'd',
                    'cpu': 'u',
                    'memory': 'a'}
        return metadata

    def _generate_random_mac(self):
        mac = [randint(0x00, 0x7f) for _ in xrange(6)]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    def create_release_api(self):
        resp = self.app.post(
            '/api/releases',
            params=json.dumps({
                'name': 'Another test release',
                'version': '1.0'
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)
        return json.loads(resp.body)

    def create_default_node(self, cluster_id=None):
        node = Node()
        node.mac = self._generate_random_mac()
        node.cluster_id = cluster_id
        self.db.add(node)
        self.db.commit()
        return node

    def create_default_role(self):
        role = Role()
        role.name = u"role Name"
        role.release = self.create_default_release()
        self.db.add(role)
        self.db.commit()
        return role

    def create_default_release(self):
        release = Release()
        release.version = randint(0, 100000000)
        release.name = u"release_name_" + str(release.version)
        release.description = u"release_desc" + str(release.version)
        release.networks_metadata = [
            {"name": "floating", "access": "public"},
            {"name": "fixed", "access": "private10"},
            {"name": "storage", "access": "private192"},
            {"name": "management", "access": "private172"},
            {"name": "other_172", "access": "private172"}
        ]
        self.db.add(release)
        self.db.commit()
        return release

    def create_default_cluster(self):
        cluster = Cluster()
        cluster.name = u"cluster_name_" + str(randint(0, 100000000))
        cluster.release = self.create_default_release()
        self.db.add(cluster)
        self.db.commit()
        return cluster

    def create_cluster_api(self):
        resp = self.app.post(
            reverse('ClusterCollectionHandler'),
            json.dumps({
                'name': 'cluster-api-' + str(randint(0, 1000000)),
                'release': self.create_default_release().id
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)
        return json.loads(resp.body)


def reverse(name, kwargs=None):
    urldict = dict(zip(urls[1::2], urls[::2]))
    url = urldict[name]
    urlregex = re.compile(url)
    for kwarg in urlregex.groupindex:
        if not kwarg in kwargs:
            raise KeyError("Invalid argument specified")
        url = re.sub(r"\(.+\)", str(kwargs[kwarg]), url, 1)
    url = re.sub(r"\??\$", "", url)
    return "/api" + url
