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

from conf import JENKINS
from jenkins import Jenkins
import json
import logging
import urllib2

logger = logging.getLogger(__package__)
J = Jenkins(JENKINS["url"])


def get_test_data(url):
    test_url = "/".join([url.rstrip("/"), 'testReport', 'api/json'])
    logger.debug("Request test data from {}".format(test_url))
    req = urllib2.Request(test_url)
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    return json.loads(s)


def get_jobs_for_view(view):
    """Return list of jobs from specified view
    """
    view_url = "/".join([JENKINS["url"], 'view', view, 'api/json'])
    logger.debug("Request view data from {}".format(view_url))
    req = urllib2.Request(view_url)
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    view_data = json.loads(s)
    jobs = [job["name"] for job in view_data["jobs"]]
    return jobs


class Build():
    def __init__(self, name, number):
        """Get build info via Jenkins API, get test info via direct HTTP
        request.

        If number is 'latest', get latest completed build.
        """

        self.name = name

        if number == 'latest':
            job_info = J.get_job_info(self.name, depth=1)
            self.number = job_info["lastCompletedBuild"]["number"]
        else:
            self.number = int(number)

        self.build_data = J.get_build_info(self.name, self.number, depth=1)
        self.url = self.build_data["url"]

    def test_data(self):
        try:
            data = get_test_data(self.url)
        except Exception as e:
            logger.warning("No test data for {0}: {1}".format(
                self.url,
                e,
            ))
            # If we failed to get any tests for the build, return
            # meta test case 'jenkins' with status 'failed'.
            data = {
                "suites": [
                    {
                        "cases": [
                            {
                                "className": "jenkins",
                                "status": "failed"
                            }
                        ]
                    }
                ]
            }

        return data

    def __str__(self):
        string = "\n".join([
            "{0}: {1}".format(*item) for item in self.build_record()
        ])
        return string

    def build_record(self):
        """Return list of pairs.

        We cannot use dictionary, because columns are ordered.
        """

        data = [
            ('number', str(self.number)),
            ('id', self.build_data["id"]),
            ('description', self.build_data["description"]),
            ('url', self.build_data["url"]),
        ]

        test_data = self.test_data()
        for suite in test_data['suites']:
            for case in suite['cases']:
                column_id = case['className'].lower().replace("_", "-")
                data.append((column_id, case['status'].lower()))

        return data
