# -*- coding: utf-8 -*-
import logging

import re
import urllib2
from api.urls import urls

logger = logging.getLogger('helpers')


class HTTPClient(object):
    def __init__(self):
        self.opener = urllib2.build_opener(urllib2.HTTPHandler)

    def get(self, url, log=False):
        req = urllib2.Request(url)
        return self._open(req, log)

    def post(self, url, data="{}", content_type="application/json", log=False):
        req = urllib2.Request(url, data=data)
        req.add_header('Content-Type', content_type)
        return self._open(req, log)

    def put(self, url, data="{}", content_type="application/json", log=False):
        req = urllib2.Request(url, data=data)
        req.add_header('Content-Type', content_type)
        req.get_method = lambda: 'PUT'
        return self._open(req, log)

    def _open(self, req, log):
        try:
            resp = self.opener.open(req)
            content = resp.read()
        except urllib2.HTTPError, error:
            content = ": ".join([str(error.code), error.read()])
        if log:
            logger.debug(content)
        return content


def reverse(name, kwargs=None):
    urldict = dict(zip(urls[1::2], urls[::2]))
    url = urldict[name]
    urlregex = re.compile(url)
    for kwarg in urlregex.groupindex:
        if not kwarg in kwargs:
            raise KeyError("Invalid argument specified")
        url = re.sub(r"\(.+\)", str(kwargs[kwarg]), url, 1)
    url = re.sub(r"\??\$", "", url)
    return "/api" + url
