#!/usr/bin/env python

import json
import subprocess
import sys

import requests

ACCEPTED_HTTP_CODE = 202

with open('/proc/cmdline', 'rt') as f:
    cmdline = f.read()
parameters = {}
for p in cmdline.split():
    name, _, value = p.partition('=')
    parameters[name] = value

api_url = parameters.get('api-url')
deployment_id = parameters.get('deployment_id')
if api_url is not None and deployment_id is not None:
    subprocess.Popen(['service', 'mcollective', 'stop'])

print "Requesting Ironic API"
print "Ironic API URL - %s" % api_url
print "Deployment ID - %s" % deployment_id

passthru = '%(api-url)s/v1/nodes/%(deployment_id)s/vendor_passthru' \
           '/pass_deploy_info' % {'api-url': api_url,
                                  'deployment_id': deployment_id}

data = {
    "address": "",
    "status": "ready",
    "error_message": "no errors"
}

result = subprocess.Popen(['hostname', '-I'], stdout=subprocess.PIPE)
ips = result.stdout.read().split()
for ip in ips:
    data['address'] = ip
    try:
        resp = requests.post(passthru, data=json.dumps(data),
                             headers={'Content-Type': 'application/json',
                                      'Accept': 'application/json'})
    except Exception:
        pass
    else:
        if resp.status_code == ACCEPTED_HTTP_CODE:
            print 'Deployment continued successfully!'
            sys.exit()

print 'Can not continue deploy, Ironic API return code was not 202.'
