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

import traceback

import web
import threading
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.query import Query
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import create_engine

from nailgun.logger import logger
from nailgun.settings import settings

db_str = "{engine}://{user}:{passwd}@{host}:{port}/{name}".format(
    **settings.DATABASE)


def make_engine():
    return create_engine(db_str, client_encoding='utf8')


thread_local_storage = threading.local()
webpy_db_engine = make_engine()


def db():
    """
    Db session object per thread
    """
    if not hasattr(thread_local_storage, 'db'):
        thread_local_storage.db = make_session(get_engine())

    return thread_local_storage.db


def get_engine():
    """
    Return one instance of the engine per thread.
    For reducing db connection overhead returns
    one instance of the engine for all webpy threads.
    """
    if is_webpy_thread():
        return webpy_db_engine

    if not hasattr(thread_local_storage, 'db_engine'):
        thread_local_storage.db_engine = make_engine()

    return thread_local_storage.db_engine


def is_webpy_thread():
    """
    web.ctx is 'threading local' object
    if it has 'env' attribute, then it's a thread for
    api request processing
    """
    return hasattr(web.ctx, 'env')


def make_session(custom_engine=None):
    session = scoped_session(
        sessionmaker(
            bind=(custom_engine or get_engine()), query_cls=NoCacheQuery))
    return session


class NoCacheQuery(Query):
    """
    Override for common Query class.
    Needed for automatic refreshing objects
    from database during every query for evading
    problems with multiple sessions
    """
    def __init__(self, *args, **kwargs):
        self._populate_existing = True
        super(NoCacheQuery, self).__init__(*args, **kwargs)


def load_db_driver(handler):
    try:
        return handler()
    except web.HTTPError:
        db().commit()
        raise
    except:
        db().rollback()
        raise
    finally:
        db().commit()
        db().expire_all()


def syncdb():
    from nailgun.api.models import Base
    Base.metadata.create_all(get_engine())


def dropdb():
    db = make_session()

    tables = [name for (name,) in db.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'")]
    for table in tables:
        db.execute("DROP TABLE IF EXISTS %s CASCADE" % table)

    # sql query to list all types, equivalent to psql's \dT+
    types = [name for (name,) in db.execute("""
        SELECT t.typname as type FROM pg_type t
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
        WHERE (t.typrelid = 0 OR (
            SELECT c.relkind = 'c' FROM pg_catalog.pg_class c
            WHERE c.oid = t.typrelid
        ))
        AND NOT EXISTS(
            SELECT 1 FROM pg_catalog.pg_type el
            WHERE el.oid = t.typelem AND el.typarray = t.oid
        )
        AND n.nspname = 'public'
        """)]
    for type_ in types:
        db.execute("DROP TYPE IF EXISTS %s CASCADE" % type_)
    db.commit()


def flush():
    import nailgun.api.models as models
    import sqlalchemy.ext.declarative as dec
    session = scoped_session(sessionmaker(bind=get_engine()))
    for attr in dir(models):
        attr_impl = getattr(models, attr)
        if isinstance(attr_impl, dec.DeclarativeMeta) \
                and not attr_impl is models.Base:
            map(session.delete, session.query(attr_impl).all())
    # for table in reversed(models.Base.metadata.sorted_tables):
    #     session.execute(table.delete())
    session.commit()
