#    Copyright 2014 Mirantis, Inc.
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
from jenkins import Job
from spreadsheet import BuildsDocument
from settings import GOOGLE_SPREADSHEET

logger = logging.getLogger(__package__)

parser = OptionParser()
parser.add_option('-j', '--job-name', dest='job_name',
                  help='Jenkins job name')
parser.add_option('-s', '--spreadsheet', dest='spreadsheet',
                  help='Google spreadsheet key', default=GOOGLE_SPREADSHEET)
(options, args) = parser.parse_args()

# Get data from Jenkins
job = Job(options.job_name)
build = None
# Look for last finished build
for b in job.builds:
    if b.get_data()['building']:
        logger.info(
            'job #{0} is building. Go to previous build'.format(b.number))
        continue
    test_report = b.test_report
    build = b
    break

if build is None:
    logger.info('finished build has not been found')
    raise

# Open google spreadsheet
doc = BuildsDocument(options.spreadsheet)
sheet = doc.get_sheet(job.name)
build_column = sheet.get_build_column_name(build.number)

# Save test report to spreadsheet
for suite in test_report['suites']:
    suite_name = suite['name']
    for case in suite['cases']:
        record = sheet.get_case_record(case['name'])
        record.content[build_column] = case['status'].lower()
        for i in range(3):
            try:
                record.Push()
                break
            except Exception as ex:
                if i > 0:
                    logger.info('failed to push changes. {0}'.format(ex.message))
                else:
                    raise ex