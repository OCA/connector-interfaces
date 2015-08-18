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


class RunTaskWizard(models.TransientModel):
    _name = 'impexp.wizard.runtask'

    flow_id = fields.Many2one('impexp.task.flow', string='Task Flow')
    task_id = fields.Many2one('impexp.task', string='Task', required=True)
    datas = fields.Binary(string='File')
    datas_fname = fields.Char(string='File Name', size=256)
    async = fields.Boolean(string='Run Asynchronously', default=True)
    attachment_id = fields.Many2one('ir.attachment', string='Result File')

    @api.onchange('flow_id')
    def onchange_flow(self):
        task_id = False
        for task in self.flow_id.task_ids:
            if task.flow_start:
                task_id = task.id
                break
        self.task_id = task_id

    @api.multi
    def run_task(self):
        self.ensure_one()
        kwargs = {'async': self.async}
        if self.datas:
            upload_name = "Upload from run task wizard: %s" \
                % self.datas_fname
            ir_attachment = self.env['ir.attachment'].\
                create({'name': upload_name,
                        'datas': self.datas,
                        'datas_fname': self.datas_fname})
            file = self.env['impexp.file'].\
                create({'attachment_id': ir_attachment.id,
                        'task_id': self.task_id.id})
            kwargs['file_id'] = file.id

        self.task_id.do_run(**kwargs)
