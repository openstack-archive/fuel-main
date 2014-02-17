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

import re
from gdata.spreadsheet import text_db
from settings import GOOGLE_LOGIN, GOOGLE_PASSWORD


class BuildsDocument(object):
    def __init__(self, spreadsheet_key):
        # connect to google docs and get spreadsheet
        self.gclient = text_db.DatabaseClient(GOOGLE_LOGIN, GOOGLE_PASSWORD)
        self.gspreadsheet = \
            self.gclient.GetDatabases(spreadsheet_key=spreadsheet_key)[0]

    def get_sheet(self, name):
        tables = self.gspreadsheet.GetTables(name=name)
        if len(tables) == 0:
            # Create new sheet
            self.gspreadsheet.client._GetSpreadsheetsClient().AddWorksheet(
                title=name, row_count=1, col_count=50,
                key=self.gspreadsheet.spreadsheet_key)
            tables = self.gspreadsheet.GetTables(name=name)
        return BuildSheet(tables.pop())


class BuildSheet:
    BUILD_COLUMN = 'b{0}'

    def __init__(self, table):
        self.table = table
        self.table.LookupFields()
        if len(self.table.fields) == 0:
            # set fields if sheet is empty
            self.table.SetFields(['name'])

    @property
    def last_build_column(self):
        if len(self.table.fields) < 2:
            return None
        else:
            return self.table.fields[1]

    def get_build_column_name(self, build_num):
        """
        Returns column name of a build.
        If there is no such column it creates another one

        It turns out name of column could not be a number.
        For ex: if name is '12' r.content returns {'_cokwr': 'PASSED'}
        So,we have to append a string to a build number and then
        use the result string as a column name
        """
        name = self.BUILD_COLUMN.format(build_num)
        if self.last_build_column != name:
            fields = self.table.fields
            fields.insert(1, name)
            self.table.SetFields(fields)
            self.table.LookupFields()
        return name
