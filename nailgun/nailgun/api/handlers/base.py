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
import uuid
from wsgiref.handlers import format_date_time
from datetime import datetime

import web
import netaddr

import nailgun.rpc as rpc
from nailgun.db import orm
from nailgun.settings import settings
from nailgun.logger import logger
from nailgun.api.models import Release
from nailgun.api.models import Cluster
from nailgun.api.models import Node
from nailgun.api.models import Network
from nailgun.api.models import Vlan
from nailgun.api.models import Task


def check_client_content_type(handler):
    content_type = web.ctx.env.get("CONTENT_TYPE", "application/json")
    if web.ctx.path.startswith("/api")\
            and not content_type.startswith("application/json"):
        raise web.unsupportedmediatype
    return handler()


def forbid_client_caching(handler):
    if web.ctx.path.startswith("/api"):
        web.header('Cache-Control',
                   'store, no-cache, must-revalidate,'
                   ' post-check=0, pre-check=0')
        web.header('Pragma', 'no-cache')
        dt = datetime.fromtimestamp(0).strftime(
            '%a, %d %b %Y %H:%M:%S GMT'
        )
        web.header('Expires', dt)
    return handler()


def content_json(func):
    def json_header(*args, **kwargs):
        web.header('Content-Type', 'application/json')
        data = func(*args, **kwargs)
        return build_json_response(data)
    return json_header


def build_json_response(data):
    web.header('Content-Type', 'application/json')
    if type(data) in (dict, list):
        return json.dumps(data, indent=4)
    return data


handlers = {}


class HandlerRegistrator(type):
    def __init__(cls, name, bases, dct):
        super(HandlerRegistrator, cls).__init__(name, bases, dct)
        if hasattr(cls, 'model'):
            key = cls.model.__name__
            if key in handlers:
                logger.warning("Handler for %s already registered" % key)
                return
            handlers[key] = cls


class JSONHandler(object):
    __metaclass__ = HandlerRegistrator

    fields = []

    def __init__(self, *args, **kwargs):
        super(JSONHandler, self).__init__(*args, **kwargs)
        self.db = orm()

    def get_object_or_404(self, model, *args, **kwargs):
        # should be in ('warning', 'Log message') format
        # (loglevel, message)
        log_404 = kwargs.pop("log_404") if "log_404" in kwargs else None
        log_get = kwargs.pop("log_get") if "log_get" in kwargs else None
        if "id" in kwargs:
            obj = self.db.query(model).get(kwargs["id"])
        elif len(args) > 0:
            obj = self.db.query(model).get(args[0])
        else:
            obj = self.db.query(model).filter(**kwargs).all()
        if not obj:
            if log_404:
                getattr(logger, log_404[0])(log_404[1])
            raise web.notfound()
        else:
            if log_get:
                getattr(logger, log_get[0])(log_get[1])
        return obj

    @classmethod
    def render(cls, instance, fields=None):
        json_data = {}
        use_fields = fields if fields else cls.fields
        if not use_fields:
            raise ValueError("No fields for serialize")
        for field in use_fields:
            if isinstance(field, (tuple,)):
                if field[1] == '*':
                    subfields = None
                else:
                    subfields = field[1:]

                value = getattr(instance, field[0])
                rel = getattr(
                    instance.__class__, field[0]).impl.__class__.__name__
                if value is None:
                    pass
                elif rel == 'ScalarObjectAttributeImpl':
                    handler = handlers[value.__class__.__name__]
                    json_data[field[0]] = handler.render(
                        value, fields=subfields
                    )
                elif rel == 'CollectionAttributeImpl':
                    if not value:
                        json_data[field[0]] = []
                    else:
                        handler = handlers[value[0].__class__.__name__]
                        json_data[field[0]] = [
                            handler.render(v, fields=subfields) for v in value
                        ]
            else:
                value = getattr(instance, field)
                if value is None:
                    json_data[field] = value
                else:
                    f = getattr(instance.__class__, field)
                    if hasattr(f, "impl"):
                        rel = f.impl.__class__.__name__
                        if rel == 'ScalarObjectAttributeImpl':
                            json_data[field] = value.id
                        elif rel == 'CollectionAttributeImpl':
                            json_data[field] = [v.id for v in value]
                        else:
                            json_data[field] = value
                    else:
                        json_data[field] = value
        return json_data
