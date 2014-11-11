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


class run_task_wizard(orm.TransientModel):
    _name = 'impexp.wizard.runtask'

    _columns = {
        'flow_id': fields.many2one('impexp.task.flow', 'Task Flow'),
        'task_id': fields.many2one('impexp.task', 'Task', required=True),
        'datas': fields.binary('File'),
        'datas_fname': fields.char('File Name', size=256),
        'async': fields.boolean('Run Asynchronously'),
        'attachment_id': fields.many2one('ir.attachment', 'Result File'),
        'state': fields.selection([('input', 'Input'), ('output', 'Output')],
                                  'State')
    }

    _defaults = {
        'state': 'input',
        'async': True,
    }

    def onchange_flow(self, cr, uid, ids, flow_id):
        flow_obj = self.pool.get('impexp.task.flow')
        flow = flow_obj.browse(cr, uid, flow_id)
        task_id = False
        for task in flow.task_ids:
            if task.flow_start:
                task_id = task.id
        return {'value': {'task_id': task_id}}

    def run_task(self, cr, uid, ids, context=None):
        run_task = self.browse(cr, uid, ids)[0]
        kwargs = {'async': run_task.async}
        file_obj = self.pool.get('impexp.file')
        if run_task.datas:
            upload_name = "Upload from run task wizard: %s" \
                % run_task.datas_fname
            ir_attachment_id = self.pool.get('ir.attachment')\
                .create(cr, uid,
                        {'name': upload_name,
                         'datas': run_task.datas,
                         'datas_fname': run_task.datas_fname})
            file_id = file_obj\
                .create(cr, uid,
                        {'attachment_id': ir_attachment_id,
                         'task_id': run_task.task_id.id})
            kwargs['file_id'] = file_id
        result_id = self.pool.get('impexp.task')\
            .do_run(cr, uid, [run_task.task_id.id], **kwargs)
        if result_id:
            res = file_obj.read(cr, uid, result_id, ['attachment_id'])
            attachment_id = res['attachment_id'][0]
            self.write(cr, uid, ids,
                       {'attachment_id': attachment_id, 'state': 'output'})
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': ids[0],
                'views': [(False, 'form')],
                'target': 'new',
            }
