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
        for ok, obj in objects.iteritems():
            new_obj = obj['model']()

            for field, value in obj["fields"].iteritems():
                #print ".".join([name.capitalize(), field])
                f = getattr(obj['model'], field)
                impl = f.impl
                fk_model = None
                if hasattr(f.comparator.prop, "argument"):
                    if hasattr(f.comparator.prop.argument, "__call__"):
                        fk_model = f.comparator.prop.argument()
                    else:
                        fk_model = f.comparator.prop.argument.class_

                if isinstance(impl,
                    orm.attributes.ScalarObjectAttributeImpl):
                    if value:
                        setattr(new_obj, field, db.query(fk_model).get(value))
                elif isinstance(impl,
                    orm.attributes.CollectionAttributeImpl):
                    if value:
                        for sub in db.query(fk_model).filter(
                                fk_model.id.in_(value)
                            ):
                            getattr(new_obj, field).append(sub)
                else:
                    setattr(new_obj, field, value)

        print new_obj
        db.add(new_obj)
        db.commit()
