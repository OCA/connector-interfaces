# -*- coding: utf-8 -*-
###############################################################################
#
#   Authors: Sebastien Beau <sebastien.beau@akretion.com>
#            David BEAL <david.beal@akretion.com>
#            Benoît Guillot <benoit.guillot@akretion.com>
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
import base64
import logging

_logger = logging.getLogger(__name__)

# name of the models usable by file.document
available_tasks = []


def add_task(name):
    if not name in available_tasks:
        available_tasks.append(name)


class file_document(orm.Model):
    _inherits = {'ir.attachment': 'attachment_id'}
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _name = "file.document"
    _description = "File Document"

    def _get_file_document_type(self, cr, uid, context=None):
        return self.get_file_document_type(cr, uid, context=context)

    def get_file_document_type(self, cr, uid, context=None):
        return [('export', 'Export')]

    def _get_tasks(self, cr, uid, context=None):
        model_obj = self.pool.get('ir.model')
        ids = model_obj.search(cr, uid,
                               [('model', 'in', available_tasks)],
                               context=context)
        res = model_obj.read(cr, uid, ids, ['model', 'name'], context=context)
        return [(r['model'], r['name']) for r in res]

    _columns = {
        'sequence': fields.integer('Sequence'),
        'ext_id': fields.char('External ID', size=64),
        'state': fields.selection(
            (('waiting', 'Waiting'),
             ('running', 'Running'),
             ('done', 'Done'),
             ('fail', 'Fail')),
            'State'),
        'active': fields.boolean('Active'),
        'date': fields.datetime(
            'Date',
            help="GMT date given by external application"),
        'direction': fields.selection(
            [('input', 'Input'), ('output', 'Output')],
            'Direction',
            help='flow direction of the file'),
        'response': fields.text(
            'Response',
            help='External application response'),
        'file_type': fields.selection(
            _get_file_document_type,
            'Type'),
        'attachment_id': fields.many2one(
            'ir.attachment',
            'Attachament',
            required=True,
            ondelete="cascade"),
        'company_id': fields.many2one(
            'res.company',
            'Company',
            required=True),
    }

    _order = 'sequence, date desc'

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company').
        _company_default_get(cr, uid, 'file.document', context=c),
        'active': 1,
        'state': 'waiting',
        'sequence': 100,
        'date': fields.datetime.now,
    }

    def check_state_file_document_scheduler(self, cr, uid, domain=None,
                                            context=None):
        if domain is None: domain = []
        domain.append(('state', '=', 'running'))
        ids = self.search(cr, uid, domain, context=context)
        if ids:
            return self.check_state(cr, uid, ids, context=context)
        return True

    def run_file_document_scheduler(self, cr, uid, domain=None, context=None):
        if domain is None: domain = []
        domain.append(('state', '=', 'waiting'))
        ids = self.search(cr, uid, domain, context=context)
        if ids:
            return self.run(cr, uid, ids, context=context)
        return True

    def run(self, cr, uid, ids, context=None):
        """
        Run the process for each file document
        """
        for file_id in ids:
            try:
                filedocument = self.browse(cr, uid, file_id, context=context)
                self._run(cr, uid, filedocument, context=context)
                if filedocument.direction == 'input':
                    filedocument.done()
            except Exception, e:
                cr.rollback()
                _logger.exception(e)
                filedocument.write({'state': 'fail', 'response': unicode(e)})
                cr.commit()
            else:
                cr.commit()
        return True

    def _run(self, cr, uid, filedocument, context=None):
        _logger.info('Start to process file document id %s' % filedocument.id)
        filedocument._set_state('running', context=context)

    def done(self, cr, uid, ids, context=None):
        _logger.info('File document id %s have been processed' % ids)
        self._set_state(cr, uid, ids, 'done', context=context)

    def _set_state(self, cr, uid, ids, state, context=None):
        for id in ids:
            self.write(cr, uid, id, {'state': state}, context=context)

    def check_state(self, cr, uid, ids, context=None):
        """ Inherit this function in your module """
        return True

    def unlink(self, cr, uid, ids, context=None):
        #attachment must be delete one by one (ORM design: S)
        for document in self.read(cr, uid, ids, ['attachment_id'],
                                  context=context):
            self.pool['ir.attachment'].unlink(
                cr, uid, [document['attachment_id'][0]], context=context)
        return True
