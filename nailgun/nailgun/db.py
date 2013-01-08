# -*- coding: utf-8 -*-


import web
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.query import Query
from sqlalchemy import create_engine

from nailgun.settings import settings

db_str = "{engine}://{path}"
if settings.DATABASE['engine'] == 'sqlite':
    db_str = db_str.format(
        engine='sqlite',
        path="/" + settings.DATABASE['name']
    )
else:
    db_str = db_str.replace(
        '{path}',
        '{user}:{passwd}@{host}:{port}/{name}'
    ).format(settings.DATABASE)

engine = create_engine(db_str)


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


def orm():
    if hasattr(web.ctx, "orm"):
        return web.ctx.orm
    else:
        web.ctx.orm = scoped_session(
            sessionmaker(bind=engine, query_cls=NoCacheQuery)
        )
        return web.ctx.orm


def load_db_driver(handler):
    web.ctx.orm = scoped_session(
        sessionmaker(bind=engine, query_cls=NoCacheQuery)
    )
    try:
        return handler()
    except web.HTTPError:
        web.ctx.orm.commit()
        raise
    except:
        web.ctx.orm.rollback()
        raise
    finally:
        web.ctx.orm.commit()


def syncdb():
    from nailgun.api.models import Base
    Base.metadata.create_all(engine)


def dropdb():
    from nailgun.api.models import Base
    Base.metadata.drop_all(engine)


def flush():
    from nailgun.api.models import Base
    session = scoped_session(sessionmaker(bind=engine))
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
        session.commit()
