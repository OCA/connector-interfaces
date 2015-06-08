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

from openerp import models, fields, api


class ImpExpChunk(models.Model):
    _name = 'impexp.chunk'
    _description = ('Structured (parsed) data from a file'
                    ' to be imported/exported')

    @api.model
    def _states(self):
        return [('new', 'New'),
                ('failed', 'Failed'),
                ('done', 'Done')]

    file_id = fields.Many2one('impexp.file', string='File')
    name = fields.Char(string='Name', required=True)
    data = fields.Text(string='Data', required=True)
    task_id = fields.Many2one(string='Related Task', related='file_id.task_id')
    state = fields.Selection(string='State', selection='_states',
                             default='new')
