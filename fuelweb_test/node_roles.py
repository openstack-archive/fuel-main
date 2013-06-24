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


class NodeRoles(object):
    def __init__(self,
                 admin_names=None,
                 other_names=None):
        self.admin_names = admin_names or []
        self.other_names = other_names or []


class Nodes(object):
    def __init__(self, environment, node_roles):
        self.admins = []
        self.others = []
        for node_name in node_roles.admin_names:
            self.admins.append(environment.node_by_name(node_name))
        for node_name in node_roles.other_names:
            self.others.append(environment.node_by_name(node_name))
        self.slaves = self.others
        self.all = self.slaves + self.admins
        self.admin = self.admins[0]

    def __iter__(self):
        return self.all.__iter__()
