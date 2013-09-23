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

import json
import inspect
from functools import wraps

from decorator import decorator

from nailgun.test.base import reverse
from nailgun.api.handlers.base import JSONHandler


class SampleGenerator(object):

    @classmethod
    def gen_sample_data(cls):
        def process(app, what_, name, obj, options, lines):
            if cls._ishandler(obj):
                lines.insert(0, cls.generate_handler_url_doc(obj))
                lines.insert(1, "")

            if lines and lines[-1]:
                lines.append("")
        return process

    @classmethod
    def _ishandler(cls, obj):
        return inspect.isclass(obj) and issubclass(obj, JSONHandler)

    @classmethod
    def _ishandlermethod(cls, obj):
        return inspect.ismethod(obj) and issubclass(obj.im_class, JSONHandler)

    @classmethod
    def generate_handler_url_doc(cls, handler):
        http_methods = ["GET", "POST", "PUT", "DELETE"]
        sample_method = None
        for field in http_methods:
            if hasattr(handler, field):
                sample_method = getattr(handler, field)
                break
        args = inspect.getargspec(sample_method).args[1:]
        test_url_data = dict([
            (arg, "%{0}%".format(arg)) for arg in args
        ])
        return "URL: **{0}**".format(
            reverse(handler.__name__, test_url_data)
        )

    @classmethod
    def gen_json_block(cls, data):
        return "\n.. code-block:: javascript\n\n{0}\n\n".format(
            "\n".join([
                "   " + s
                for s in json.dumps(data, indent=4).split("\n")
            ])
        )


def setup(app):
    app.connect(
        'autodoc-process-docstring',
        SampleGenerator.gen_sample_data()
    )
