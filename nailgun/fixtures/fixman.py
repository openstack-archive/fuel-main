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
                f = getattr(obj['model'], field)
                impl = f.impl
                print dir(f.comparator)
                print type(f.comparator.prop)
                # if isinstance(impl,
                #     orm.attributes.ScalarObjectAttributeImpl):
                #     if value:
                #         fk = db.query(known_objects[field]).get(value)
                #         setattr(new_obj, field, fk)
                # elif isinstance(impl, 
                #     orm.attributes.CollectionAttributeImpl):
                #     pass
                #     #for sub in db.query(known_models[field]).filter(known_models[field].id.in_(value)):
                #     #    getattr(new_obj, field).append(sub)
                # else:
                #     setattr(new_obj, field, value)

        # db.add(new_obj)
        # db.commit()
