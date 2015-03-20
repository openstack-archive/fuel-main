#    Copyright 2015 Mirantis, Inc.
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

from launchpadlib.launchpad import Launchpad


class LaunchpadBug(object):
    def __init__(self, bug_id):
        self.launchpad = Launchpad.login_anonymously('just testing',
                                                     'production',
                                                     '.cache')
        self.bug = self.launchpad.bugs[int(bug_id)]

    @property
    def targets(self):
        return [{'project': str(task.bug_target_name).split('/')[0],
                 'milestone': str(task.milestone).split('/')[-1],
                 'status': str(task.status)} for task in self.bug_tasks]

    def get_duplicate_of(self):
        bug = self.bug
        duplicates = []
        while bug.duplicate_of and bug.id not in duplicates:
            duplicates.append(bug.id)
            bug = self.launchpad.load(str(bug.duplicate_of))
        return LaunchpadBug(bug.id)

    def __getattr__(self, item):
        return self.bug.__getattr__(item)
