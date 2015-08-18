# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 initOS GmbH & Co. KG (<http://www.initos.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from xlrd import open_workbook
import logging

from openerp import models, api
from openerp.addons.connector_flow.task.csv_import import TableRowImport

_logger = logging.getLogger(__name__)


class XlsImport(TableRowImport):
    """Parses an XLS file and stores the lines as chunks"""

    def _row_generator(self, file_data, config=None):
        wb = open_workbook(file_contents=file_data)
        # use only first sheet
        sheet = wb.sheet_by_index(0)
        for row in range(sheet.nrows):
            yield [sheet.cell(row, col).value for col in range(sheet.ncols)]


class XlsImportTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(XlsImportTask, self)._get_available_tasks() \
            + [('xls_import', 'XLS Import')]

    def xls_import_class(self):
        return XlsImport
