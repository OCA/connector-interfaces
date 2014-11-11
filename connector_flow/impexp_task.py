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
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession
from ast import literal_eval


def impexp_related_action(session, job):
    # Redirect the call to OpenERP model
    return session.pool.get('impexp.task') \
        .related_action(session.cr, session.uid,
                        job=job, context=session.context)


@job
@related_action(action=impexp_related_action)
def run_task(session, model_name, ids, **kwargs):
    return session.pool.get('impexp.task') \
        .run_task(session.cr, session.uid, ids, **kwargs)


class impexp_task_transition(orm.Model):
    _name = 'impexp.task.transition'
    _description = 'Transition between tasks'

    def _get_available_tasks(self, cr, uid, context=None):
        return []

    _columns = {
        'task_from_id': fields.many2one('impexp.task',
                                        'Output-producing Task'),
        'task_to_id': fields.many2one('impexp.task',
                                      'Input-consuming Task'),
    }


class impexp_task_flow(orm.Model):
    _name = 'impexp.task.flow'
    _description = 'A flow of tasks that are connected by transitions'

    _columns = {
        'name': fields.char('Name', required=True),
        'task_ids': fields.one2many('impexp.task', 'flow_id',
                                    'Tasks in Flow')
    }


class impexp_task(orm.Model):
    _name = 'impexp.task'
    _description = 'A wrapper class for an import/export task'

    def _get_available_tasks(self, cr, uid, context=None):
        return []

    def _get_available_types(self, cr, uid, context=None):
        return [('file', 'File'), ('chunk', 'Chunk')]

    _columns = {
        'name': fields.char('Name', required=True),
        'task': fields.selection(_get_available_tasks, string='Task'),
        'config': fields.text('Configuration'),
        'last_start': fields.datetime('Starting Time of the Last Run'),
        'last_finish': fields.datetime('Finishing Time of'
                                       'the Last Successful Run'),
        'max_retries': fields.integer('Maximal Number of Re-tries'
                                      ' If Run Asynchronously',
                                      required=True),
        'flow_id': fields.many2one('impexp.task.flow', 'Task Flow'),
        'transitions_out_ids': fields.one2many('impexp.task.transition',
                                               'task_from_id',
                                               'Outgoing Transitions'),
        'transitions_in_ids': fields.one2many('impexp.task.transition',
                                              'task_to_id',
                                              'Incoming Transitions'),
        'flow_start': fields.boolean('Start of a Task Flow'),
    }

    _defaults = {
        'max_retries': 1,
    }

    def _check_unique_flow_start(self, cr, uid, ids, context=None):
        """Check that there is at most one task that starts the
           flow in a task flow"""
        for task in self.browse(cr, uid, ids, context=context):
            domain = [('flow_id', '=', task.flow_id.id),
                      ('flow_start', '=', True)]
            flow_start_ids = self.search(cr, uid, domain)
            if len(flow_start_ids) > 1:
                return False
        return True

    _constraints = [
        (_check_unique_flow_start, 'The start of a task flow has to be unique',
         ['flow_id', 'flow_start'])
    ]

    def _config(self, cr, uid, ids, context=None):
        """Parse task configuration"""
        config = self.read(cr, uid, ids, ['config'])[0]['config']
        if config:
            return literal_eval(config)
        return {}

    def do_run(self, cr, uid, task_ids, context=None, async=True, **kwargs):
        if async:
            method = run_task.delay
            assert len(task_ids) == 1
            task_data = self.read(cr, uid, task_ids[0],
                                  ['name', 'max_retries'])
            kwargs.update({'description': task_data['name'],
                           'max_retries': task_data['max_retries']})
        else:
            method = run_task
        result = method(ConnectorSession(cr, uid, context=context),
                        self._name, task_ids, async=async, **kwargs)
        # If we run asynchronously, we ignore the result
        #  (which is the UUID of the job in the queue).
        if not async:
            return result

    def do_run_flow(self, cr, uid, flow_id,
                    context=None, async=True, **kwargs):
        flow_obj = self.pool.get('impexp.task.flow')
        flow = flow_obj.browse(cr, uid, flow_id)
        task_id = False
        for task in flow.task_ids:
            if task.flow_start:
                task_id = task.id
        if not task_id:
            raise Exception('Flow %d has no start' % flow_id)
        return self.do_run(cr, uid, [task_id],
                           context=context, async=True, **kwargs)

    def get_task_instance(self, cr, uid, ids):
        task_list = self.browse(cr, uid, ids)
        assert len(task_list) == 1

        task_method = task_list[0].task
        task_class = getattr(self, task_method + '_class')()
        return task_class(cr, uid, ids)

    def run_task(self, cr, uid, ids, **kwargs):
        task_instance = self.get_task_instance(cr, uid, ids)
        config = self._config(cr, uid, ids)
        return task_instance.run(config=config, **kwargs)

    def related_action(self, cr, uid, job=None, **kwargs):
        task_instance = self.get_task_instance(cr, uid, job.args[1])
        return task_instance.related_action(job=job, **kwargs)
