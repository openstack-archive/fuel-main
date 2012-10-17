# -*- coding: utf-8 -*-

import json
import logging
import unittest
import cStringIO

from nailgun.test.base import BaseHandlers
from nailgun.fixtures.fixman import upload_fixture
from nailgun.api.models import Release, Node


class TestFixture(BaseHandlers):

    fixtures = ['sample_environment']

    def test_upload_working(self):
        check = self.db.query(Node).all()
        self.assertEqual(len(list(check)), 9)

    def test_custom_fixture(self):
        data = u'''[{
            "pk": 1,
            "model": "nailgun.release",
            "fields": {
                "name": "CustomFixtureRelease",
                "version": "0.0.1",
                "description": "Sample release for testing",
                "networks_metadata": [
                  {"name": "floating", "access": "public"},
                  {"name": "fixed", "access": "private10"},
                  {"name": "management", "access": "private172"},
                  {"name": "storage", "access": "private192"}
                ]
            }
        }]'''
        upload_fixture(cStringIO.StringIO(data))
        check = self.db.query(Release).filter(
            Release.name == u"CustomFixtureRelease"
        )
        self.assertEqual(len(list(check)), 1)
