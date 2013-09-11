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
from mock import patch
import time
import re

from shotgun.config import Config

class TestConfig(TestCase):

	def test_timestamp(self):
		t = time.localtime()
		with patch('shotgun.config.time') as MockedTime:
			MockedTime.localtime.return_value = t
			MockedTime.strftime.side_effect = time.strftime
			conf = Config({})
			stamped = conf._timestamp("sample")
		self.assertEquals(
			stamped,
			"sample-{0}".format(time.strftime('%Y-%m-%d_%H-%M-%S', t))
		)

	def test_target_timestamp(self):
		conf = Config({
			"target": "/tmp/sample",
			"timestamp": True
		})
		assert bool(
			re.search(
				ur"\/tmp\/sample\-[\d]{4}\-[\d]{2}\-[\d]{2}_([\d]{2}\-){2}[\d]{2}",
				conf.target
			)
		)

