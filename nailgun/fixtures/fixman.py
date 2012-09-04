# -*- coding: utf-8 -*-

import json

from api import models
from sqlalchemy import orm, ext

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
                fk_model = None
                if hasattr(f.comparator.prop, "argument") \
                    and hasattr(f.comparator.prop.argument, "__call__"):
                    fk_model = f.comparator.prop.argument()

                if isinstance(impl,
                    orm.attributes.ScalarObjectAttributeImpl):
                    print field
                    print dir(f)
                elif isinstance(impl, 
                    orm.attributes.CollectionAttributeImpl):
                    for sub in db.query(fk_model).filter(fk_model.id.in_(value)):
                        getattr(new_obj, field).append(sub)
                else:
                    setattr(new_obj, field, value)

        #db.add(new_obj)
        #db.commit()
