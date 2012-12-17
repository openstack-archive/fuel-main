# -*- coding: utf-8 -*-

import json

import web

from nailgun.db import orm
from nailgun.api.models import Task
from nailgun.api.handlers.base import JSONHandler


class TaskHandler(JSONHandler):
    fields = (
        "id",
        "cluster",
        "uuid",
        "name",
        "message",
        "status",
        "progress"
    )
    model = Task

    def GET(self, task_id):
        web.header('Content-Type', 'application/json')
        q = orm().query(Task)
        task = q.get(task_id)
        if not task:
            return web.notfound()
        return json.dumps(
            self.render(task),
            indent=4
        )

    def DELETE(self, task_id):
        q = orm().query(Task)
        task = q.get(task_id)
        if not task:
            return web.notfound()
        if task.status not in ("ready", "error"):
            raise web.badrequest("You cannot delete running task manually")
        for subtask in task.subtasks:
            orm().delete(subtask)
        orm().delete(task)
        orm().commit()
        raise web.webapi.HTTPError(
            status="204 No Content",
            data=""
        )


class TaskCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        user_data = web.input(cluster_id=None)
        if user_data.cluster_id:
            tasks = orm().query(Task).filter_by(
                cluster_id=user_data.cluster_id).all()
        else:
            tasks = orm().query(Task).all()
        return json.dumps(map(
            TaskHandler.render,
            tasks), indent=4)
