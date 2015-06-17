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


class ImpExpFile(models.Model):
    _name = 'impexp.file'
    _description = 'Wrapper for a file to be imported/exported'

    @api.model
    def _states(self):
        return [('new', 'New'),
                ('failed', 'Failed'),
                ('done', 'Done')]

    attachment_id = fields.Many2one('ir.attachment', string='Attachment',
                                    required=True)
    task_id = fields.Many2one('impexp.task', string='Task')
    state = fields.Selection(string='State', selection='_states',
                             default='new', required=True)
