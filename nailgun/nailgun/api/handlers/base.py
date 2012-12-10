# -*- coding: utf-8 -*-

import json
import uuid
from wsgiref.handlers import format_date_time
from datetime import datetime

import web
import netaddr

import nailgun.rpc as rpc
from nailgun.settings import settings
from nailgun.logger import logger
from nailgun.api.models import Release
from nailgun.api.models import Cluster
from nailgun.api.models import Node
from nailgun.api.models import Network
from nailgun.api.models import Vlan
from nailgun.api.models import Task
from nailgun.network import manager as netmanager


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

handlers = {}


class HandlerRegistrator(type):
    def __init__(cls, name, bases, dct):
        super(HandlerRegistrator, cls).__init__(name, bases, dct)
        if hasattr(cls, 'model'):
            key = cls.model.__name__
            if key in handlers:
                logger.warning("Handler for %s already registered" % key)
                return
                #raise Exception("Handler for %s already registered" % key)
            handlers[key] = cls


class JSONHandler(object):
    __metaclass__ = HandlerRegistrator

    fields = []

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
                    pass
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
