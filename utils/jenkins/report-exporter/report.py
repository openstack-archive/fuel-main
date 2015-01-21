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

import logging
from optparse import OptionParser

from builds import Build
from builds import get_jobs_for_view
from spreadsheet import Document

logger = logging.getLogger(__package__)
logger.addHandler(logging.StreamHandler())


def page_for_build(build_name):
    """Get version-independent lower-case page name.
    """
    return build_name[build_name.index("system_test."):].lower()


def report_build(document, name, number='latest'):
    """If number='latest', report last completed build.

    """
    page = document.get_page(page_for_build(name))

    build = Build(name, number)

    if page.build_exists(build.number):
        # We have to use 'build.number' and not 'number' variable
        # here, because number can be specified as 'latest'.
        # build.number is properly resolved in Build.__init__()

        logger.debug("Build {0} exists".format(build.number))
        return None

    page.add_build(build.build_record())


def report_view(document, view):
        jobs = get_jobs_for_view(view)
        system_test_jobs = [name for name in jobs if '.system_test.' in name]

        failures = []

        for name in system_test_jobs:
            try:
                report_build(document, name, 'latest')
            except Exception as e:
                logger.debug(
                    "Failed to report {0} with error: {1}".format(name, e)
                )
                failures.append(name)

        # Retry failed
        for name in failures:
            logger.debug("Retry failed {0}".format(name))
            try:
                report_build(document, name, 'latest')
            except Exception as e:
                logger.debug(
                    "Failed again to report {0}: {1}".format(name, e)
                )
            else:
                failures.remove(name)

        logger.debug("Failures: {0}".format(",".join(failures)))

        return system_test_jobs, failures


def main():

    parser = OptionParser(
        description="Publish results of Jenkins build to Google Spreadsheet."
        " See conf.py for configuration."
    )
    parser.add_option('-j', '--job-name', dest='job_name',
                      help='Jenkins job name')
    parser.add_option('-N', '--build-number', dest='build_number',
                      default='latest',
                      help='Jenkins build number')
    parser.add_option('--view', dest='view',
                      help='Jenkins view name')
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Enable debug output")

    (options, args) = parser.parse_args()

    if options.verbose:
        logger.setLevel(logging.DEBUG)

    d = Document()

    if options.job_name:
        report_build(d, options.job_name, options.build_number)
        return options.job_name

    if options.view:
        jobs, failures = report_view(d, options.view)
        exit(len(failures))


if __name__ == "__main__":
    main()
