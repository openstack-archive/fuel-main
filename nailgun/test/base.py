import json
from paste.fixture import TestApp
from random import randint
from unittest.case import TestCase
import re
from sqlalchemy.orm.events import orm
from api.models import engine, Node, Release, Cluster, Role
from api.urls import urls
from db import dropdb, syncdb, flush
from manage import app


class BaseHandlers(TestCase):
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

    def create_default_node(self):
        node = Node()
        node.mac = u"ASDFGHJKLMNOPR"
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
