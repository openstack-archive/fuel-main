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

from mock import Mock
from mock import patch

from nailgun.api.validators.cluster import ClusterValidator
from nailgun.errors import errors
from nailgun.test.base import BaseTestCase


class TestClusterValidator(BaseTestCase):
    def setUp(self):
        self.cluster_data = '{"name": "test"}'
        self.release_data = '{"release": 1}'

    def test_cluster_exists_validation(self):
        with patch('nailgun.api.validators.cluster.db', Mock()) as db:
            db.return_value.query.return_value.filter_by.\
                return_value.first.return_value = 'cluster'
            self.assertRaises(errors.AlreadyExists,
                              ClusterValidator.validate, self.cluster_data)

    def test_cluster_non_exists_validation(self):
        with patch('nailgun.api.validators.cluster.db', Mock()) as db:
            try:
                db.return_value.query.return_value.filter_by.\
                    return_value.first.return_value = None
                ClusterValidator.validate(self.cluster_data)
            except errors.AlreadyExists as e:
                self.fail('Cluster exists validation failed: {0}'.format(e))

    def test_release_exists_validation(self):
        with patch('nailgun.api.validators.cluster.db', Mock()) as db:
            db.return_value.query.return_value.get.\
                return_value = None
            self.assertRaises(errors.InvalidData,
                              ClusterValidator.validate, self.release_data)

    def test_release_non_exists_validation(self):
        with patch('nailgun.api.validators.cluster.db', Mock()) as db:
            try:
                db.return_value.query.return_value.get.\
                    return_value = 'release'
                ClusterValidator.validate(self.release_data)
            except errors.InvalidData as e:
                self.fail('Release exists validation failed: {0}'.format(e))