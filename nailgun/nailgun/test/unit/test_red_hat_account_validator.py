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

from nailgun.api.validators.redhat import RedHatAccountValidator
from nailgun.errors import errors
from nailgun.test.base import BaseTestCase


class TestRedHatAccountValidator(BaseTestCase):
    def test_valid_account_data(self):
        """


        """
        accounts_data = [
            '{"release_id": 1, "license_type": "rhsm",'
            ' "username": "u", "password": "p"}',
            '{"release_id": 1, "license_type": "rhn", '
            '"username": "u", "password": "p", '
            '"satellite": "s", "activation_key": "k"}',
        ]
        for account_data in accounts_data:
            self.assertNotRaises(errors.InvalidData,
                                 RedHatAccountValidator.validate,
                                 account_data)

    def test_invalid_account_data(self):
        accounts_data = [
            'account',
            '{"release_id": 1, "license_type": "personal"}',
            '{"release_id": 1, "license_type": "rhsm",'
            ' "username": "u"}',
            '{"release_id": 1, "license_type": "rhsm",'
            '"password": "p"}',
            '{"release_id": 1, "license_type": "rhn", '
            '"username": "u", "password": "p", ',
            '{"release_id": 1, "license_type": "rhn", '
            '"username": "u", "password": "p", '
            '"satellite": "s"}',
            '{"release_id": 1, "license_type": "rhn", '
            '"username": "u", "password": "p", '
            '"activation_key": "k"}',
        ]

        for account_data in accounts_data:
            self.assertRaises(errors.InvalidData,
                              RedHatAccountValidator.validate,
                              account_data)
