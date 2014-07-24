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
import gdata.spreadsheet
from jenkins import Job
from spreadsheet import BuildsDocument
from settings import GOOGLE_SPREADSHEET

logger = logging.getLogger(__package__)
logger.addHandler(logging.StreamHandler())

parser = OptionParser()
parser.add_option('-j', '--job-name', dest='job_name',
                  help='Jenkins job name')
parser.add_option('-s', '--spreadsheet', dest='spreadsheet',
                  help='Google spreadsheet key', default=GOOGLE_SPREADSHEET)
parser.add_option("-v", "--verbose",
                  action="store_true", dest="verbose", default=False,
                  help="Enable debug output")

(options, args) = parser.parse_args()

if options.verbose:
    logger.setLevel(logging.DEBUG)

# Get data from Jenkins
job = Job(options.job_name)
build = job.last_finished_build()

# Open google spreadsheet
doc = BuildsDocument(options.spreadsheet)

# Remove leading version-dependent symbols
sheet_name = job.name[job.name.index("system_test."):]
logger.info("Updating sheet {0}".format(sheet_name))

test_report = build.test_report

sheet = doc.get_sheet(sheet_name)
gd_client = doc.gspreadsheet.client._GetSpreadsheetsClient()
gd_sheet = filter(
    lambda e: sheet_name in e.title.text,
    gd_client.GetWorksheetsFeed(key=options.spreadsheet).entry
).pop()
gd_sheet_id = gd_sheet.id.text.rsplit('/', 1)[1]
gd_rows = \
    {r.title.text: r for r in gd_client.GetListFeed(
        key=options.spreadsheet, wksht_id=gd_sheet_id).entry}

# Get or create build column
build_column = sheet.get_build_column_name(build.number, build.get_iso_number())

# Save test report to spreadsheet
for suite in test_report['suites']:
    suite_name = suite['name']
    for case in suite['cases']:
        case_name = case['name']
        case_status = case['status'].lower()
        if case_name in gd_rows:
            # Updated row
            row = gd_rows[case_name]
            # Create new cell instance
            new_cell = gdata.spreadsheet.Custom()
            new_cell.column = build_column
            new_cell.text = case_status
            # Add new cell and put changes to sheet
            row.custom[build_column] = new_cell
            for lnk in row.link:
                if lnk.rel == 'edit':
                    converter = gdata.spreadsheet.SpreadsheetsListFromString
                    gd_client.Put(row, lnk.href, converter=converter)
        else:
            # Insert new row
            row_data = {'name': case_name, build_column: case_status}
            gd_client.InsertRow(row_data, options.spreadsheet,
                                wksht_id=gd_sheet_id)
