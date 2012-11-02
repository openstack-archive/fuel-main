# -*- coding: utf-8 -*-

import json
import os.path
import logging

from nailgun.settings import settings
from nailgun.api import models
from sqlalchemy import orm
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)
db = orm.scoped_session(orm.sessionmaker(bind=models.engine))()


def upload_fixture(fileobj):
    try:
        fixture = json.load(fileobj)
    except:
        raise Exception("Invalid fixture!")

    known_objects = {}

    for obj in fixture:
        pk = obj["pk"]
        model_name = obj["model"].split(".")[1]
        obj['model'] = getattr(models, model_name.capitalize())
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

            try:
                db.add(new_obj)
                db.commit()
            except IntegrityError as e:
                logger.info("Integrity error while uploading"
                            "\n=== object: %s"
                            "\n=== exception trace: %s" % (obj, e))


def upload_fixture_from_file(filename):
    if os.path.exists(filename):
        with open(filename, "r") as fileobj:
            upload_fixture(fileobj)


def upload_fixtures():
    fns = []
    for path in settings.FIXTURES_TO_UPLOAD:
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(os.path.dirname(__file__), path)
        fns.append(path)

    for fn in fns:
        try:
            upload_fixture_from_file(abs_fn)
        except Exception as e:
            logger.error("Error while uploading fixture: "
                         "\nfilename: %s\n"
                         "\nexception trace: %s" % (abs_fn, e))
            raise e
        else:
            logger.info("Fixture has been uploaded from file: %s" % abs_fn)
