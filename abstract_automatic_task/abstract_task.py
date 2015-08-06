# -*- coding: utf-8 -*-
###############################################################################
#
#   abstract_automatic_task for OpenERP
#   Author: Benoît Guillot <benoit.guillot@akretion.com>
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
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class automatic_task(orm.Model):
    _name = "automatic.task"
    _description = "Automatic Task"

    def _get_task_type(self, cr, uid, context=None):
        return self.get_task_type(cr, uid, context=context)

    def get_task_type(self, cr, uid, context=None):
        return []

    _columns = {
        'cron_ids': fields.many2many(
            'ir.cron',
            'cron_automatic_task_rel',
            'cron_id',
            'task_id',
            'Cron Tasks'),
        'active': fields.boolean('Active'),
        'type': fields.selection(
            _get_task_type,
            'Type'),
        #maybe use a fields.reference to various task to go easily
        #from the automatic_task to the various task
        #in that case be careful that the relation is one2one
        #between auto_task and the various task
    }

    _defaults = {
        'active': 1,
    }

    def _run_all_task_for_cron(self, cr, uid, cron_id, context=None):
        for name, model in self.pool.models.iteritems():
            if model._inherits.get('automatic.task') == 'automatic_task_id' \
               and name != 'abstrack.task':
                task_ids = model.search(cr, uid,
                                        [('cron_ids', 'in', [cron_id])],
                                        context=context)
                model.run(cr, uid, task_ids, context=context)
        return True


class abstract_task(orm.AbstractModel):
    _name = "abstrack.task"
    _description = "Abstrack Task"
    _inherits = {'automatic.task': 'automatic_task_id'}

    _columns ={
        'automatic_task_id': fields.many2one(
            'automatic.task',
            string='Automatic Taks',
            required=True,
            ondelete="cascade"),
        'last_exe_date': fields.datetime(
            'Last execution date'),
    }

    def create_cron_from_abstract(self, cr, uid, ids, context=None):
        model_data_obj = self.pool['ir.model.data']
        cron_obj = self.pool['ir.cron']
        cron_ids = []
        for task in self.browse(cr, uid, ids, context=context):
            nextcall = datetime.now() + timedelta(minutes=20)
            nextcall_fmt = datetime.strftime(nextcall,
                                             DEFAULT_SERVER_DATETIME_FORMAT)
            create_vals = {
                'auto_task_ids': [(4, task.automatic_task_id.id)],
                'active': True,
                'model': 'automatic.task',
                'function': '_run_all_task_for_cron',
                'name': task.name,
                'nextcall': nextcall_fmt,
                'doall': False,
                'numbercall': -1,
            }
            cron_id = cron_obj.create(cr, uid, create_vals, context=context)
            write_vals = {'args': '[%s]' % cron_id}
            cron_obj.write(cr, uid, [cron_id], write_vals, context=context)
            cron_ids.append(cron_id)
        #if several crons are created, open a tree view
        #instead of a form maybe useless because it's rare
        # to call this button with several task_ids
        view_id = False
        if len(cron_ids) > 1:
            view_name = 'ir_cron_view_tree'
            view_mode = 'tree,form'
            res_id = cron_ids
            target = False
        else:
            view_name = 'automatic_cron_form_view'
            res_id = cron_ids[0]
            view_mode = 'form'
            target = 'new'
            model_data_id = model_data_obj.search(
                cr, uid, [['model', '=', 'ir.ui.view'],
                          ['name', '=', 'automatic_cron_form_view']],
                context=context)
            if model_data_id:
                view_id = model_data_obj.read(
                    cr, uid, model_data_id, fields=['res_id'])[0]['res_id']
        return {
            'name': 'Cron',
            'view_type': 'form',
            'view_mode': view_mode,
            'view_id': view_id and [view_id] or False,
            'res_model': 'ir.cron',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': target,
            'res_id': res_id,
        }


class ir_cron(orm.Model):
    _inherit = "ir.cron"

    _columns = {
        'auto_task_ids': fields.many2many(
            'automatic.task',
            'cron_automatic_task_rel',
            'task_id',
            'cron_id',
            'Task'),
    }

    def save_and_close_cron(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
