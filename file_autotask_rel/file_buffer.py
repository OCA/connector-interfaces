# -*- coding: utf-8 -*-
###############################################################################
#
#   file_autotask_rel for OpenERP
#   Authors: Sebastien Beau <sebastien.beau@akretion.com>
#   Copyright 2013 Akretion
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import fields, orm

available_tasks = []

#TODO improve
def add_task(name):
    if not name in available_tasks:
        available_tasks.append(name)


class file_buffer(orm.Model):
    _inherit = "file.buffer"

    def _get_tasks(self, cr, uid, context=None):
        model_obj = self.pool.get('ir.model')
        ids = model_obj.search(cr, uid,
                               [('model', 'in', available_tasks)],
                               context=context)
        res = model_obj.read(cr, uid, ids, ['model', 'name'], context=context)
        return [(r['model'], r['name']) for r in res]

    _columns = {
        'task_id': fields.reference('Task', selection=_get_tasks, size=128),
    }
