# -*- coding: utf-8 -*-

import json

from api import models
from sqlalchemy import orm

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

                if isinstance(
                        impl,
                        orm.attributes.ScalarObjectAttributeImpl):
                    if value:
                        fk_fields[field] = (value, fk_model)
                        #setattr(new_obj, field, db.query(fk_model).get(value))
                elif isinstance(
                        impl,
                        orm.attributes.CollectionAttributeImpl):
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

            db.add(new_obj)
            db.commit()
