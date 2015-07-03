#!/usr/bin/env python

import httplib2
import json
import subprocess
import sys

api_url = sys.argv[1]
deployment_id = sys.argv[2]

print "Requesting Ironic API"
print "Ironic API URL - %s" % api_url
print "Deployment ID - %s" % deployment_id

passthru = 'http://%(api_url)s/v1/nodes/%(deployment_id)s/vendor_passthru' \
           '/pass_deploy_info' % {'api_url': sys.argv[1],
                                  'deployment_id': sys.argv[2]}

data = {
    "address": "",
    "status": "ready",
    "error_message": "no errors"
}

result = subprocess.Popen(['hostname', '-I'], stdout=subprocess.PIPE)
ips = result.stdout.read().split()
h = httplib2.Http()
for ip in ips:
    data['address'] = ip
    resp, content = h.request(passthru, "POST", body=json.dumps(data),
                              headers={'Content-Type': 'application/json',
                                       'Accept': 'application/json'})
    if resp.status == 202:
        print 'Success!'
        sys.exit()

print 'Can not continue deploy, Ironic API return code was not 202.'
