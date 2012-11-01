# -*- coding: utf-8 -*-

import json

import web

from nailgun.api.models import Release
from nailgun.api.handlers.base import JSONHandler


class ReleaseHandler(JSONHandler):
    fields = (
        "id",
        "name",
        "version",
        "description"
    )
    model = Release

    def GET(self, release_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Release)
        release = q.filter(Release.id == release_id).first()
        if not release:
            return web.notfound()
        return json.dumps(
            self.render(release),
            indent=4
        )

    def PUT(self, release_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Release)
        release = q.filter(Release.id == release_id).first()
        if not release:
            return web.notfound()
        # additional validation needed?
        data = Release.validate_json(web.data())
        # /additional validation needed?
        for key, value in data.iteritems():
            setattr(release, key, value)
        web.ctx.orm.commit()
        return json.dumps(
            self.render(release),
            indent=4
        )

    def DELETE(self, release_id):
        release = web.ctx.orm.query(Release).filter(
            Release.id == release_id
        ).first()
        if not release:
            return web.notfound()
        web.ctx.orm.delete(release)
        web.ctx.orm.commit()
        raise web.webapi.HTTPError(
            status="204 No Content",
            data=""
        )


class ReleaseCollectionHandler(JSONHandler):
    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps(map(
            ReleaseHandler.render,
            web.ctx.orm.query(Release).all()
        ), indent=4)

    def POST(self):
        web.header('Content-Type', 'application/json')
        data = Release.validate(web.data())
        release = Release()
        for key, value in data.iteritems():
            setattr(release, key, value)
        web.ctx.orm.add(release)
        web.ctx.orm.commit()
        raise web.webapi.created(json.dumps(
            ReleaseHandler.render(release),
            indent=4
        ))
