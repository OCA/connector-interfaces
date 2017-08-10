# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from cPickle import dumps
from psycopg2 import Binary
from openerp import fields, models
try:
    from openerp.addons.connector.queue.job import Job
except ImportError:
    import logging
    logging.error('Couldn\'t import connector')


class AuditlogRule(models.Model):
    _inherit = 'auditlog.rule'

    log_async = fields.Boolean(
        'Asynchronous', help='Log asynchronously. This make the system feel '
        'faster because the user doesn\'t have to wait for the logging to '
        'finish in order to continue. Be cautious with this if you really '
        'exact logs, as the log might be off if the databases changes between '
        'a call to a logged function and the logging itself, which can happen '
        'on very busy instances'
    )

    def create_logs(
            self, uid, res_model, res_ids, method, old_values=None,
            new_values=None, additional_log_values=None,
    ):
        if self.pool._auditlog_async_cache[res_model] and\
           not self.env.context.get('auditlog_sync'):
            # don't use the delay function because it uses the orm and won't
            # be much faster than writing the log itself
            queue_job = Job(
                func=create_logs_async, model_name=self._name,
                args=(uid, res_model, res_ids, method),
                kwargs=dict(old_values=old_values, new_values=new_values,
                            additional_log_values=additional_log_values),
            )
            queue_job.user_id = uid
            self.env.cr.execute(
                'insert into queue_job '
                '(state, priority, retry, max_retries, exc_info, user_id, '
                'company_id, result, date_enqueued, date_started, date_done, '
                'func_name, active, uuid, name, func_string, '
                'date_created, model_name, func) '
                'values '
                '(%(state)s, %(priority)s, %(retry)s, %(max_retries)s, '
                '%(exc_info)s, %(user_id)s, %(company_id)s, %(result)s, '
                '%(date_enqueued)s, %(date_started)s, %(date_done)s, '
                '%(func_name)s, %(active)s, %(uuid)s, %(name)s, '
                '%(func_string)s, %(date_created)s, %(model_name)s, %(func)s)',
                dict(
                    queue_job.__dict__,
                    func=Binary(dumps(
                        (queue_job.func_name, queue_job.args, queue_job.kwargs)
                    )),
                    active=True,
                    uuid=queue_job.uuid,
                    name='Asynchronous logging on %s(%s)' % (
                        res_model, res_ids,
                    ),
                    func_string=queue_job.func_string,
                )
            )
        else:
            return super(AuditlogRule, self).create_logs(
                uid, res_model, res_ids, method, old_values=old_values,
                new_values=new_values,
                additional_log_values=additional_log_values
            )

    def _register_hook(self, cr, ids=None):
        # model => async
        cr.execute(
            'select m.model, r.log_async from '
            'auditlog_rule r join ir_model m on r.model_id=m.id'
        )
        self.pool._auditlog_async_cache = dict(cr.fetchall())
        return super(AuditlogRule, self)._register_hook(cr, ids=ids)


def create_logs_async(
    self, model_name, uid, log_model_name, log_model_res_ids,
    log_method, old_values=None, new_values=None,
    additional_log_values=None,
):
    return self.env[model_name].sudo(uid).with_context(auditlog_sync=True)\
        .create_logs(
            uid, log_model_name, log_model_res_ids, log_method,
            old_values=old_values, new_values=new_values,
            additional_log_values=additional_log_values
        )
