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

from openerp.osv import orm, fields


class imp_exp_chunk(orm.Model):
    _name = 'impexp.chunk'
    _description = 'Structured (parsed) data from a file' +\
                   ' to be imported/exported'

    _columns = {
        'file_id': fields.many2one('impexp.file', 'File'),
        'name': fields.char('Name', required=True),
        'data': fields.text('Data', required=True),
        'task_id': fields.related('file_id', 'task_id', 'Related Task'),
        'state': fields.selection([('new', 'New'),
                                   ('failed', 'Failed'),
                                   ('done', 'Done')],
                                  'State',
                                  required=True),
    }

    _defaults = {
        'state': 'new',
    }
