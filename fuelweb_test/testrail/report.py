#!/usr/bin/env python
#
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

import functools
import re

from logging import DEBUG
from optparse import OptionParser

from builds import Build
from builds import get_jobs_for_view
from settings import logger
from settings import TestRailSettings
from testrail_client import TestRailProject


class TestResult():
    def __init__(self, name, group, status, duration, url=None,
                 version=None, description=None):
        self.name = name
        self.group = group
        self._status = status
        self.duration = duration
        self.url = url
        self.version = version
        self.description = description
        self.available_statuses = {
            'passed': ['passed', 'fixed'],
            'failed': ['failed', 'regression'],
            'skipped': ['skipped']
        }

    @property
    def status(self):
        for s in self.available_statuses.keys():
            if self._status in self.available_statuses[s]:
                return s
        logger.error('Unsupported result status: "{0}"!'.format(self._status))
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    def __str__(self):
        result_dict = {
            'name': self.name,
            'group': self.group,
            'status': self.status,
            'duration': self.duration,
            'url': self.url,
            'version': self.version,
            'description': self.description
        }
        return str(result_dict)


def retry(count=3):
    def wrapped(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            i = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except:
                    i += 1
                    if i >= count:
                        raise
        return wrapper
    return wrapped


def get_downstream_builds(jenkins_build_data):
    return [{'name': b['jobName'], 'number': b['buildNumber']}
            for b in jenkins_build_data['subBuilds']]


def get_version(jenkins_build_data):
    parameters = [a['parameters'] for a in jenkins_build_data['actions']
                  if 'parameters' in a.keys()][0]
    iso_link = [p['value'] for p in parameters if
                p['name'].lower() == 'magnet_link'][0]
    return (re.search(r'.*\bfuel-(\d+\.\d+)-(\d+)-.*', iso_link).group(1),
            int(re.search(r'.*\bfuel-(\d+\.\d+)-(\d+)-.*', iso_link).group(2)))


@retry(count=3)
def get_tests_results(systest_build):
    tests_results = []
    test_build = Build(systest_build['name'], systest_build['number'])
    for test in test_build.test_data()['suites'][0]['cases']:
        test_result = TestResult(
            name=test['name'],
            group=test['className'],
            status=test['status'].lower(),
            duration='{0}s'.format(int(test['duration']) + 1),
            url='{0}testReport/(root)/{1}/'.format(test_build.url,
                                                   test['name']),
            version='_'.join([test_build.build_data["id"]] +
                             (test_build.build_data["description"]
                              or test['name']).split()),
            description=test_build.build_data["description"] or
                test['name'],
        )
        tests_results.append(test_result)
    return tests_results


def publish_results(project, test_plan, tests_suite, config_id, results):
    test_run_id = [run['id'] for run in test_plan['entries'][0]['runs'] if
                   config_id in run['config_ids']][0]
    tests = project.get_tests(run_id=test_run_id)
    results_to_publish = []

    for result in results:
        test = project.get_test_by_group(run_id=test_run_id,
                                         group=result.group,
                                         tests=tests)
        if not test:
            logger.error("Test for '{0}' group not found: {1}".format(
                result.group, result.url))
            continue
        existing_results_versions = [r['version'] for r in
                                     project.get_results_for_test(test['id'])]
        if result.version not in existing_results_versions:
            results_to_publish.append(result)
    try:
        if len(results_to_publish) > 0:
            project.add_results_for_cases(run_id=test_run_id,
                                          tests_suite=tests_suite,
                                          tests_results=results_to_publish)
    except:
        logger.error('Failed to add new results for tests: {0}'.format(
            [r.group for r in results_to_publish]
        ))
        raise
    return results_to_publish


def main():

    parser = OptionParser(
        description="Publish results of Jenkins build to TestRail."
        " See conf.py for configuration."
    )
    parser.add_option('-j', '--job-name', dest='job_name', default=None,
                      help='Jenkins swarm runner job name')
    parser.add_option('-N', '--build-number', dest='build_number',
                      default='latest',
                      help='Jenkins swarm runner build number')
    parser.add_option("-w", "--view", dest="jenkins_view", default=False,
                      help="Get system tests jobs from Jenkins view")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Enable debug output")

    (options, args) = parser.parse_args()

    if options.verbose:
        logger.setLevel(DEBUG)

    tests_results_centos = []
    tests_results_ubuntu = []
    case_group = TestRailSettings.test_suite

    if options.jenkins_view:
        jobs = get_jobs_for_view(options.jenkins_view)
        tests_jobs = [{'name': j, 'number': 'latest'}
                      for j in jobs if 'system_test' in j]
        runner_job = [j for j in jobs if 'runner' in j][0]
        runner_build = Build(runner_job, 'latest')
    elif options.job_name:
        runner_build = Build(options.job_name, options.build_number)
        tests_jobs = get_downstream_builds(runner_build.build_data)
    else:
        logger.error("Please specify either Jenkins swarm runner job name (-j)"
                     " or Jenkins view with system tests jobs (-w). Exiting..")
        return

    milestone, iso_number = get_version(runner_build.build_data)

    for systest_build in tests_jobs:
        if 'centos' in systest_build['name'].lower():
            tests_results_centos.extend(get_tests_results(systest_build))
        elif 'ubuntu' in systest_build['name'].lower():
            tests_results_ubuntu.extend(get_tests_results(systest_build))

    project = TestRailProject(url=TestRailSettings.url,
                              user=TestRailSettings.user,
                              password=TestRailSettings.password,
                              project=TestRailSettings.project)

    test_plan_name = '{milestone} {case_group} iso #{iso_number}'.format(
        milestone=milestone, case_group=case_group, iso_number=iso_number)

    operation_systems = [{'name': config['name'], 'id': config['id']}
                         for config in project.get_config_by_name(
                             'Operation System')['configs']]

    if not project.get_plan_by_name(test_plan_name):
        plan_entries = [project.test_run_struct(
            name='{case_group}'.format(case_group=case_group),
            suite=case_group,
            milestone=milestone,
            description='Results of system tests ({case_group}) on iso # '
                        '"{iso_number}"'.format(case_group=case_group,
                                                iso_number=iso_number),
            config_ids=[os['id']],
            include_all=True) for os in operation_systems]

        test_plan = project.add_plan(test_plan_name,
                                     description='',
                                     milestone=milestone,
                                     entires=[
                                         {
                                             'suite_id': project.get_suite(
                                                 case_group)['id'],
                                             'config_ids': [os['id'] for os in
                                                            operation_systems],
                                             'runs': plan_entries
                                         }
                                     ])
    else:
        test_plan = project.get_plan_by_name(test_plan_name)

    logger.debug('Uploading tests results to TestRail...')
    for os in operation_systems:
        if 'centos' in os['name'].lower():
            tests_results_centos = publish_results(project=project,
                                                   test_plan=test_plan,
                                                   tests_suite=case_group,
                                                   config_id=os['id'],
                                                   results=tests_results_centos
                                                   )
        if 'ubuntu' in os['name'].lower():
            tests_results_ubuntu = publish_results(project=project,
                                                   test_plan=test_plan,
                                                   tests_suite=case_group,
                                                   config_id=os['id'],
                                                   results=tests_results_ubuntu
                                                   )

    logger.debug('Added new results for tests (CentOS): {tests}'.format(
        tests=[r.group for r in tests_results_centos]
    ))
    logger.debug('Added new results for tests (Ubuntu): {tests}'.format(
        tests=[r.group for r in tests_results_ubuntu]
    ))
    logger.info('Report URL: {0}'.format(test_plan['url']))


if __name__ == "__main__":
    main()
