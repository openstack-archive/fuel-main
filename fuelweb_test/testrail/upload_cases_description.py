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

import re

from logging import DEBUG
from optparse import OptionParser
from proboscis import TestProgram

from fuelweb_test.run_tests import import_tests
from settings import logger
from settings import TestRailSettings
from testrail_client import TestRailProject


def get_tests_descriptions(milestone_id, tests_include, tests_exclude):
    import_tests()

    tests = []

    for case in TestProgram().cases:
        if tests_include:
            if tests_include not in case.entry.home.func_name:
                logger.debug("Skipping '{0}' test because it doesn't contain '"
                             "{1}' in method name".format(
                                 case.entry.home.func_name,
                                 tests_include))
                continue
        if tests_exclude:
            if tests_exclude in case.entry.home.func_name:
                logger.debug("Skipping '{0}' test because it contains '{1}' in"
                             "method name".format(case.entry.home.func_name,
                                                  tests_exclude))
                continue

        docstring = case.entry.home.func_doc or ''
        docstring = '\n'.join([s.strip() for s in docstring.split('\n')])

        steps = [{"content": s, "expected": "pass"} for s in
                 docstring.split('\n') if s and s[0].isdigit()]

        test_duration = re.search(r'Duration\s+(\d+[s,m])\b', docstring)
        test_case = {
            "title": docstring.split('\n')[0] or case.entry.home.func_name,
            "type_id": 1,
            "milestone_id": milestone_id,
            "priority_id": 5,
            "estimate": test_duration.group(1) if test_duration else "3m",
            "refs": "",
            "custom_test_group": case.entry.home.func_name,
            "custom_test_case_description": docstring or " ",
            "custom_test_case_steps": steps
        }
        tests.append(test_case)
    return tests


def upload_tests_descriptions(testrail_project, section_id, tests):
    tests_suite = testrail_project.get_suite_by_name(
        TestRailSettings.tests_suite)
    existing_cases = [case['custom_test_group'] for case in
                      testrail_project.get_cases(suite_id=tests_suite['id'],
                                                 section_id=section_id)]
    for test_case in tests:
        if test_case['custom_test_group'] in existing_cases:
            logger.debug('Skipping uploading "{0}" test case because it '
                         'already exists in "{1}" tests section.'.format(
                             test_case['custom_test_group'],
                             TestRailSettings.tests_suite))
            continue

        logger.debug('Uploading test "{0}" to TestRail project "{1}", '
                     'suite "{2}", section "{3}"'.format(
                         test_case["custom_test_group"],
                         TestRailSettings.project,
                         TestRailSettings.tests_suite,
                         TestRailSettings.tests_section))
        testrail_project.add_case(section_id=section_id, case=test_case)


def main():
    project = TestRailProject(
        url=TestRailSettings.url,
        user=TestRailSettings.user,
        password=TestRailSettings.password,
        project=TestRailSettings.project
    )

    testrail_section = project.get_section_by_name(
        suite_id=project.get_suite_by_name(TestRailSettings.tests_suite)['id'],
        section_name=TestRailSettings.tests_section
    )

    testrail_milestone = project.get_milestone_by_name(
        name=TestRailSettings.milestone)

    tests_descriptions = get_tests_descriptions(
        milestone_id=testrail_milestone['id'],
        tests_include=TestRailSettings.tests_include,
        tests_exclude=TestRailSettings.tests_exclude
    )

    upload_tests_descriptions(testrail_project=project,
                              section_id=testrail_section['id'],
                              tests=tests_descriptions)

if __name__ == '__main__':
    parser = OptionParser(
        description="Upload tests cases to TestRail. "
                    "See settings.py for configuration."
    )
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Enable debug output")

    (options, args) = parser.parse_args()

    if options.verbose:
        logger.setLevel(DEBUG)

    main()
