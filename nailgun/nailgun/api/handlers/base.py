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
from nailgun.db import db
from nailgun import notifier
from nailgun.settings import settings
from nailgun.errors import errors
from nailgun.logger import logger
from nailgun.api.models import Release
from nailgun.api.models import Cluster
from nailgun.api.models import Node
from nailgun.api.models import Network
from nailgun.api.models import Vlan
from nailgun.api.models import Task
from nailgun.api.serializers.base import BasicSerializer
from nailgun.api.validators.base import BasicValidator


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
    validator = BasicValidator
    serializer = BasicSerializer

    fields = []

    def __init__(self):
        self.serializer.load_handlers(handlers)

    @classmethod
    def render(cls, instance, fields=None):
        return cls.serializer.serialize(
            instance,
            fields=fields or cls.fields
        )

    def checked_data(self, validate_method=None):
        try:
            if validate_method:
                data = validate_method(web.data())
            else:
                data = self.validator.validate(web.data())
        except (
            errors.InvalidInterfacesInfo,
            errors.InvalidMetadata
        ) as exc:
            notifier.notify("error", str(exc))
            raise web.badrequest(message=str(exc))
        except (
            errors.AlreadyExists
        ) as exc:
            err = web.conflict()
            err.message = exc.message
            raise err
        except (
            errors.InvalidData,
            Exception
        ) as exc:
            raise web.badrequest(message=str(exc))
        return data

    def get_object_or_404(self, model, *args, **kwargs):
        # should be in ('warning', 'Log message') format
        # (loglevel, message)
        log_404 = kwargs.pop("log_404") if "log_404" in kwargs else None
        log_get = kwargs.pop("log_get") if "log_get" in kwargs else None
        if "id" in kwargs:
            obj = db().query(model).get(kwargs["id"])
        elif len(args) > 0:
            obj = db().query(model).get(args[0])
        else:
            obj = db().query(model).filter(**kwargs).all()
        if not obj:
            if log_404:
                getattr(logger, log_404[0])(log_404[1])
            raise web.notfound()
        else:
            if log_get:
                getattr(logger, log_get[0])(log_get[1])
        return obj
