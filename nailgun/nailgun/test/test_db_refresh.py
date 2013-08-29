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

from datetime import datetime
from unittest import TestCase

from paste.fixture import TestApp
from sqlalchemy.orm.events import orm

from nailgun.api.models import Node
from nailgun.db import engine
from nailgun.db import flush
from nailgun.db import NoCacheQuery
from nailgun.wsgi import build_app


class TestDBRefresh(TestCase):

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
        self.db.query(Node).filter(
            Node.id == node.id
        ).first()
        self.assertEquals(node.mac, u"12345678")
