import json
import urllib
import httplib
from urlparse import urlparse


def query_api(url, method='GET', params={}):
    if method not in ('GET', 'POST', 'PUT', 'DELETE'):
        raise ValueError("Invalid method %s" % method)

    parsed_url = urlparse(url)

    body = None
    path = parsed_url.path
    if method in ('POST', 'PUT'):
        body = urllib.urlencode(params)
    elif params:
        path = "%s?%s" % (path, urllib.urlencode(params))

    conn = httplib.HTTPConnection(parsed_url.netloc)
    conn.request(method, path, body)
    response = conn.getresponse()
    raw_data = response.read()

    data = None
    try:
        data = json.loads(raw_data)
    except ValueError:
        pass

    return (response.status, data)
