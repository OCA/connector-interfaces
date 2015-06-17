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

from openerp import models, api
from openerp.addons.connector_flow.task.abstract_task \
    import AbstractChunkWriteTask


class CsvPartnerExport(AbstractChunkWriteTask):

    def run(self, config=None, async=True):
        # We will store the data that we want to export
        #  as list of lists, corresponding to the structured rows
        #  in the export file
        result_list = [['Name', 'ZIP Code']]
        for p in self.session.env['res.partner'].search([]):
            result_list.append([p.name, p.zip])

        return self.write_and_run_chunk(result_list, 'List of all res.partner',
                                        async=async)


class CsvPartnerExportTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(CsvPartnerExportTask, self)._get_available_tasks() \
            + [('csv_partner_export', 'CSV Partner Export')]

    def csv_partner_export_class(self):
        return CsvPartnerExport
