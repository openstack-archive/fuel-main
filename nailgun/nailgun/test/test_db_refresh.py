# -*- coding: utf-8 -*-

from datetime import datetime

from unittest import TestCase

from paste.fixture import TestApp
from sqlalchemy.orm.events import orm

from nailgun.api.models import Node
from nailgun.db import engine
from nailgun.db import dropdb, syncdb, flush, NoCacheQuery
from nailgun.wsgi import build_app


class TestDBRefresh(TestCase):
    @classmethod
    def setUpClass(cls):
        dropdb()
        syncdb()

    def setUp(self):
        self.app = TestApp(build_app().wsgifunc())
        self.db = orm.scoped_session(
            orm.sessionmaker(bind=engine, query_cls=NoCacheQuery)
        )()
        self.db2 = orm.scoped_session(
            orm.sessionmaker(bind=engine, query_cls=NoCacheQuery)
        )()
        self.default_headers = {
            "Content-Type": "application/json"
        }
        flush()

    def test_session_update(self):
        node = Node()
        node.mac = u"ASDFGHJKLMNOPR"
        node.timestamp = datetime.now()
        self.db.add(node)
        self.db.commit()

        node2 = self.db2.query(Node).filter(
            Node.id == node.id
        ).first()
        node2.mac = u"12345678"
        self.db2.add(node2)
        self.db2.commit()
        node1 = self.db.query(Node).filter(
            Node.id == node.id
        ).first()
        self.assertEquals(node.mac, u"12345678")
