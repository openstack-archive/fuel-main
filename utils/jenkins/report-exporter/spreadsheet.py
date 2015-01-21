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

from conf import GOOGLE
from gdata.spreadsheet import text_db
import logging

logger = logging.getLogger(__package__)


class Document():
    def __init__(self):
        self.gclient = text_db.DatabaseClient(
            GOOGLE["user"],
            GOOGLE["password"],
        )
        self.gspreadsheet = self.gclient.GetDatabases(
            spreadsheet_key=GOOGLE["key"]
        )[0]

    def get_page(self, name):
        tables = self.gspreadsheet.GetTables(name=name)
        if len(tables) > 0:
            logger.debug("Use worksheet {0}".format(name))
        else:
            # Create new worksheet
            logger.debug("Create new worksheet {0}".format(name))
            self.gspreadsheet.client._GetSpreadsheetsClient().AddWorksheet(
                title=name,
                row_count=1,
                col_count=50,
                key=self.gspreadsheet.spreadsheet_key,
            )
            tables = self.gspreadsheet.GetTables(name=name)

        return Page(tables.pop())


class Page():
    def __init__(self, table):
        self.table = table
        self.table.LookupFields()

    def build_exists(self, number):
        records = self.table.FindRecords(
            "number == {0}".format(number)
        )
        return records

    def add_build(self, build_record):
        """Adds build to the table

        If there is a row with same build id and build number,
        do nothing.
        """
        build_number = build_record[0][1]
        if self.build_exists(build_number):
            logger.debug(
                "Build {0} is already there".format(build_number)
            )
            return None

        logger.debug("Create record "
                     "for build {0}".format(build_number))
        self.update_columns(build_record)
        self.table.AddRecord(dict(build_record))
        logger.info("Created record "
                    "for build {0}".format(build_number))

    def update_columns(self, build_record):
        """Update table columns

        If current build has more tests than the previous one
        we extend the table by appending more columns.

        """
        fields_changed = False

        fields = self.table.fields
        for key in [key for key, value in build_record if key not in fields]:
            fields_changed = True
            fields.append(key)

        if fields_changed:
            logger.debug("New columns: {}".format(fields))
            self.table.SetFields(fields)
            logger.debug("New columns added")

        return fields
