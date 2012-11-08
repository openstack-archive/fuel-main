# -*- coding: utf-8 -*-

import json

import web

from nailgun.task.task import Task
from nailgun.api.handlers.base import JSONHandler


class TaskHandler(JSONHandler):
    fields = (
        "id",
        "cluster",
        "uuid",
        "name",
        "error",
        "status",
        "progress"
    )
    model = Task

    def GET(self, task_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Task)
        task = q.filter(Task.id == task_id).first()
        if not task:
            return web.notfound()
        return json.dumps(
            self.render(task),
            indent=4
        )

    def DELETE(self, task_id):
        q = web.ctx.orm.query(Task)
        task = q.filter(Task.id == task_id).first()
        if not task:
            return web.notfound()
        if task.status not in ("ready", "error"):
            raise web.badrequest("You cannot delete running task manually")
        web.ctx.orm.delete(task)
        web.ctx.orm.commit()
        raise web.webapi.HTTPError(
            status="204 No Content",
            data=""
        )


class TaskCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        user_data = web.input(cluster_id=None)
        if user_data.cluster_id:
            tasks = web.ctx.orm.query(Task).filter_by(
                cluster_id=user_data.cluster_id).all()
        else:
            tasks = web.ctx.orm.query(Task).all()
        return json.dumps(map(
            TaskHandler.render,
            tasks), indent=4)
