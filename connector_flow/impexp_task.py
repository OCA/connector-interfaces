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

from openerp import models, fields, api, exceptions, _

from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession
from ast import literal_eval


def impexp_related_action(session, job):
    # Redirect the call to OpenERP model
    return session.env['impexp.task'].related_action(job=job)


@job
@related_action(action=impexp_related_action)
def run_task(session, model_name, ids, **kwargs):
    return session.env['impexp.task'].browse(ids).run_task(**kwargs)


class ImpExpTaskTransition(models.Model):
    _name = 'impexp.task.transition'
    _description = 'Transition between tasks'

    task_from_id = fields.Many2one('impexp.task',
                                   string='Output-producing Task')
    task_to_id = fields.Many2one('impexp.task', string='Input-consuming Task')


class ImpExpTaskFlow(models.Model):
    _name = 'impexp.task.flow'
    _description = 'A flow of tasks that are connected by transitions'

    name = fields.Char(string='Name', required=True)
    task_ids = fields.One2many('impexp.task', 'flow_id',
                               string='Tasks in Flow')


class ImpExpTask(models.Model):
    _name = 'impexp.task'
    _description = 'A wrapper class for an import/export task'

    @api.model
    def _get_available_tasks(self):
        return []

    name = fields.Char(string='Name', required=True)
    task = fields.Selection(selection='_get_available_tasks', string='Task')
    config = fields.Text(string='Configuration')
    last_start = fields.Datetime(string='Starting Time of the Last Run')
    last_finish = fields.Datetime(string='Finishing Time of the '
                                         'Last Successful Run')
    max_retries = fields.Integer(string='Maximal Number of Re-tries'
                                        ' If Run Asynchronously',
                                 required=True, default=1)
    flow_id = fields.Many2one('impexp.task.flow', string='Task Flow')
    transitions_out_ids = fields.One2many('impexp.task.transition',
                                          'task_from_id',
                                          string='Outgoing Transitions')
    transitions_in_ids = fields.One2many('impexp.task.transition',
                                         'task_to_id',
                                         string='Incoming Transitions')
    flow_start = fields.Boolean(string='Start of a Task Flow')

    @api.one
    @api.constrains('flow_start', 'flow_id')
    def _check_unique_flow_start(self):
        """Check that there is at most one task that starts the
           flow in a task flow"""
        if self.flow_start:
            flow_start_count = self.search_count(
                [('flow_id', '=', self.flow_id.id),
                 ('flow_start', '=', True)])
            if 1 < flow_start_count:
                raise exceptions. \
                    ValidationError(_('The start of a task flow '
                                      'has to be unique'))

    @api.multi
    def _config(self):
        """Parse task configuration"""
        self.ensure_one()
        config = self.config
        if config:
            return literal_eval(config)
        return {}

    @api.multi
    def do_run(self, async=True, **kwargs):
        self.ensure_one()
        if async:
            method = run_task.delay
            kwargs.update({'description': self.name,
                           'max_retries': self.max_retries})
        else:
            method = run_task
        result = method(ConnectorSession.from_env(self.env),
                        self._name, self.ids, async=async, **kwargs)
        # If we run asynchronously, we ignore the result
        #  (which is the UUID of the job in the queue).
        if not async:
            return result

    @api.model
    def do_run_flow(self, flow_id, **kwargs):
        flow = self.env['impexp.task.flow'].browse(flow_id)
        flow.ensure_one()
        start_task = False
        for task in flow.task_ids:
            if task.flow_start:
                start_task = task
                break
        if not start_task:
            raise Exception(_('Flow %d has no start') % flow_id)
        return start_task.do_run(**kwargs)

    @api.multi
    def get_task_instance(self):
        self.ensure_one()
        task_method = self.task
        task_class = getattr(self, task_method + '_class')()
        return task_class(self.env.cr, self.env.uid, self.ids)

    @api.multi
    def run_task(self, **kwargs):
        self.ensure_one()
        task_instance = self.get_task_instance()
        config = self._config()
        return task_instance.run(config=config, **kwargs)

    @api.model
    def related_action(self, job=None, **kwargs):
        assert job, "Job argument missing"
        task_instance = self.browse(job.args[1]).get_task_instance()
        return task_instance.related_action(job=job, **kwargs)
