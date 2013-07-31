#!/usr/bin/env python

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import sys
sys.path.insert(0, '/usr/share/rhsm/')

import json
import socket
import traceback

from rhsm.connection import UEPConnection
from subscription_manager.managercli import handle_exception


def get_licenses(username, password):
    uep = UEPConnection(username=username, password=password)
    owner_key = uep.getOwnerList(username)[0]['key']
    pool_list = uep.getPoolsList(owner=owner_key)

    avail_licenses = 0
    licenses = []
    for pool in pool_list:
        license_info = {}

        if 'OpenStack' in pool['productName']:
            license_info['quantity'] = pool['quantity']
            license_info['consumed'] = pool['consumed']
            license_info['product_name'] = pool['productName']
            license_info['id'] = pool['id']
            license_info['active_subscription'] = pool['activeSubscription']

            # subscriptionSubKey is master for physical hosts
            # subscriptionSubKey is derived for virtual hosts
            license_info['type'] = pool['subscriptionSubKey']

            if pool['subscriptionSubKey'] == 'master':
                license_info['free'] = int(pool['quantity']) - int(pool['consumed'])
                if pool['activeSubscription']:
                    avail_licenses += license_info['free']

            licenses.append(license_info)

    return {
        'openstack' : licenses,
        'openstack_licenses_physical_hosts_count' : avail_licenses
    }

if __name__ == "__main__":
    username = sys.argv[1]
    password = sys.argv[2]

    try:
        licenses = get_licenses(username, password)
        print json.dumps(licenses)
    except Exception, exc:
        handle_exception(traceback.format_exc(), exc)
