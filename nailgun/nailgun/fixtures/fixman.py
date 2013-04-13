# -*- coding: utf-8 -*-

import json
import os.path
import itertools
from datetime import datetime

import sqlalchemy.types
from nailgun.settings import settings
from nailgun.api import models
from sqlalchemy import orm
from nailgun.db import orm as ormgen
from nailgun.logger import logger
from sqlalchemy.exc import IntegrityError

db = ormgen()


def upload_fixture(fileobj):
    fixture = json.load(fileobj)

    known_objects = {}

    for obj in fixture:
        pk = obj["pk"]
        model_name = obj["model"].split(".")[1]

        try:
            model = itertools.dropwhile(
                lambda m: not hasattr(models, m),
                [model_name.capitalize(),
                 "".join(map(lambda n: n.capitalize(), model_name.split("_")))]
            ).next()
        except StopIteration:
            raise Exception("Couldn't find model {0}".format(model_name))

        obj['model'] = getattr(models, model)

        # Check if it's already uploaded
        obj_from_db = db.query(obj['model']).get(pk)
        if obj_from_db:
            logger.info("Fixture model '%s' with pk='%s' already"
                        " uploaded. Skipping", model_name, pk)
            continue
        known_objects.setdefault(model_name, {})[pk] = obj

    for name, objects in known_objects.iteritems():
        for pk, obj in objects.iteritems():
            new_obj = obj['model']()

            fk_fields = {}
            for field, value in obj["fields"].iteritems():
                # print "%s.%s = %s" % (
                #     name.capitalize(),
                #     field,
                #     value
                # )
                f = getattr(obj['model'], field)
                impl = f.impl
                fk_model = None
                if hasattr(f.comparator.prop, "argument"):
                    if hasattr(f.comparator.prop.argument, "__call__"):
                        fk_model = f.comparator.prop.argument()
                    else:
                        fk_model = f.comparator.prop.argument.class_

                if isinstance(impl, orm.attributes.ScalarObjectAttributeImpl):
                    if value:
                        fk_fields[field] = (value, fk_model)
                        #setattr(new_obj, field, db.query(fk_model).get(value))
                elif isinstance(impl, orm.attributes.CollectionAttributeImpl):
                    if value:
                        fk_fields[field] = (value, fk_model)
                        # for sub in db.query(fk_model).filter(
                        #         fk_model.id.in_(value)
                        #     ):
                        #     getattr(new_obj, field).append(sub)
                elif isinstance(
                    f.property.columns[0].type, sqlalchemy.types.DateTime
                ):
                    if value:
                        setattr(
                            new_obj,
                            field,
                            datetime.strptime(value, "%d-%m-%Y %H:%M:%S")
                        )
                    else:
                        setattr(
                            new_obj,
                            field,
                            datetime.now()
                        )
                else:
                    setattr(new_obj, field, value)

            for field, data in fk_fields.iteritems():
                if isinstance(data[0], int):
                    setattr(new_obj, field, db.query(data[1]).get(data[0]))
                elif isinstance(data[0], list):
                    for v in data[0]:
                        getattr(new_obj, field).append(
                            db.query(data[1]).get(v)
                        )
            db.add(new_obj)
            db.commit()
            # UGLY HACK for testing
            if new_obj.__class__.__name__ == 'Node':
                new_obj.attributes = models.NodeAttributes()
                db.commit()
                new_obj.attributes.volumes = \
                    new_obj.volume_manager.gen_default_volumes_info()
                db.commit()


def upload_fixtures():
    fns = []
    for path in settings.FIXTURES_TO_UPLOAD:
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                path))
        fns.append(path)

    for fn in fns:
        with open(fn, "r") as fileobj:
            upload_fixture(fileobj)
        logger.info("Fixture has been uploaded from file: %s" % fn)


def dump_fixture(model_name):
    dump = []
    app_name = 'nailgun'
    model = getattr(models, model_name.capitalize())
    for obj in db.query(model).all():
        obj_dump = {}
        obj_dump['pk'] = getattr(obj, model.__mapper__.primary_key[0].name)
        obj_dump['model'] = "%s.%s" % (app_name, model_name)
        obj_dump['fields'] = {}
        dump.append(obj_dump)
        for prop in model.__mapper__.iterate_properties:
            if isinstance(prop, sqlalchemy.orm.ColumnProperty):
                field = str(prop.key)
                value = getattr(obj, field)
                if value is None:
                    continue
                if not isinstance(value, (
                        list, dict, str, unicode, int, float, bool)):
                    value = ""
                obj_dump['fields'][field] = value
    print json.dumps(dump, indent=4)
