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


class VlansActor(object):
    """Contains all logic to manage vlans
    """

    def __init__(self, config):
        """
        @config - list or tuple of (iface, vlan) pairs
        """
        self.config = config

    def __enter__(self):
        for iface, vlans in self.config.iteritems():
            yield str(iface)
            for vlan in vlans:
                if vlan > 0:
                    yield '{0}.{1}'.format(iface, vlan)

    def __exit__(self, type, value, trace):
        pass
