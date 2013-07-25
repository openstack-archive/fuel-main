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


class BasicSerializer(object):

    handlers = {}

    @classmethod
    def load_handlers(cls, handlers):
        if not cls.handlers:
            cls.handlers = handlers
        return cls.handlers

    @classmethod
    def serialize(cls, instance, fields=None):
        data_dict = {}
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
                    handler = cls.handlers[value.__class__.__name__]
                    data_dict[field[0]] = handler.render(
                        value, fields=subfields
                    )
                elif rel == 'CollectionAttributeImpl':
                    if not value:
                        data_dict[field[0]] = []
                    else:
                        handler = cls.handlers[value[0].__class__.__name__]
                        data_dict[field[0]] = [
                            handler.render(v, fields=subfields) for v in value
                        ]
            else:
                value = getattr(instance, field)
                if value is None:
                    data_dict[field] = value
                else:
                    f = getattr(instance.__class__, field)
                    if hasattr(f, "impl"):
                        rel = f.impl.__class__.__name__
                        if rel == 'ScalarObjectAttributeImpl':
                            data_dict[field] = value.id
                        elif rel == 'CollectionAttributeImpl':
                            data_dict[field] = [v.id for v in value]
                        else:
                            data_dict[field] = value
                    else:
                        data_dict[field] = value
        return data_dict
