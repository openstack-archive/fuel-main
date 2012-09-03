# -*- coding: utf-8 -*-

import json
import web


class BasicValidator(object):
    @classmethod
    def validate_json(cls, data):
        if data:
            try:
                res = json.loads(data)
            except:
                raise web.webapi.badrequest(
                    message="Invalid json format!"
                )
            return res
        return data

    @classmethod
    def validate(cls, data):
        raise NotImplementedError("You should override this method")
