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

from nailgun.api.validators.cluster import AttributesValidator
from nailgun.errors import errors
from nailgun.test.base import BaseTestCase


class TestAttributesValidator(BaseTestCase):
    def test_generated_attributes_validation(self):
        self.assertRaises(errors.InvalidData,
                          AttributesValidator.validate,
                          '{"generated": {"name": "test"}}')

    def test_editable_attributes_validation(self):
        self.assertRaises(errors.InvalidData,
                          AttributesValidator.validate,
                          '{"editable": "name"}')

    def test_valid_attributes(self):
        valid_attibutes = [
            '{"editable": {"name":"test"}}',
            '{"name":"test"}'
        ]

        for attributes in valid_attibutes:
            self.assertNotRaises(errors.InvalidData,
                                 AttributesValidator.validate,
                                 attributes)
