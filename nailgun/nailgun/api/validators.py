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
                    message="Invalid json format"
                )
        else:
            raise web.webapi.badrequest(
                message="Empty request received"
            )
        return res

    @classmethod
    def validate(cls, data):
        raise NotImplementedError("You should override this method")
