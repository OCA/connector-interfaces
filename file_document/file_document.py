# -*- coding: utf-8 -*-
###############################################################################
#
#   file_document for OpenERP
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

# name of the models usable by file.document
available_tasks = []
def add_task(name):
    if not name in available_tasks:
        available_tasks.append(name)


class file_document(orm.Model):
    _inherits = {'ir.attachment': 'attachment_id'}
    _name = "file.document"
    _description = "File Document"

    def _get_file_document_type(self, cr, uid, context=None):
        return self.get_file_document_type(cr, uid, context=context)

    def get_file_document_type(self, cr, uid, context=None):
        return []

    def _get_tasks(self, cr, uid, context=None):
        model_obj = self.pool.get('ir.model')
        ids = model_obj.search(cr, uid,
                               [('model', 'in', available_tasks)],
                               context=context)
        res = model_obj.read(cr, uid, ids, ['model', 'name'], context=context)
        return [(r['model'], r['name']) for r in res]

    _columns = {
        'ext_id': fields.char('External ID', size=64),
        'state': fields.selection((('waiting','Waiting'),
                                   ('running','Running'),
                                   ('done','Done'),
                                   ('fail','Fail')), 'State'),
        'active': fields.boolean('Active'), #still needed?
        'date': fields.datetime('Date',
                    help="GMT date given by external application"),
        'direction': fields.selection([('input', 'Input'),
                                       ('output', 'Output')], 'Direction',
                                      help='flow direction of the file'),
        'response': fields.text('Response',
                        help='External application response'),
        'file_type': fields.selection(_get_file_document_type, 'Type'),
        'attachment_id': fields.many2one('ir.attachment', 'Attachament',
                            required=True, ondelete="cascade"),
    }

    _order = 'date desc'

    _defaults = {
        'active': 1,
        'state': 'waiting',
        'date': fields.date.context_today,
    }

#    def get_file(self, cr, uid, file_document_id, context=None):
#        """
#        Fonction that return the content of the attachment
#        :param int file_id : id of the file document
#        :rtype: str
#        :return: the content attachment
#        """
#        attach_obj = self.pool['ir.attachment']
#        attachment_id = attach_obj.search(cr, uid,
#                                          [('res_model','=','file.document'),
#                                           ('res_id','=', file_document_id)],
#                                          context=context)
#        if not attachment_id:
#            return False
#        attachment = attach_obj.browse(cr, uid, attachment_id[0], context=context)
#        return base64.decodestring(attachment.datas)
#
#    def create_file_document_attachment(self, cr, uid, file_document_id, datas,
#                                      file_name, context=None, extension='csv',
#                                      prefix_file_name='report'):
#        """
#        Create file attachment to file.document object
#        :param int file_document_id:
#        :param str datas: file content
#        :param str file_name: file name component
#        :param str extension: file extension
#        :param str prefix_file_name:
#        :rtype: boolean
#        :return: True
#        """
#        if context is None: context = {}
#        attach_obj = self.pool['ir.attachment']
#        context.update({'default_res_id': file_document_id,
#                        'default_res_model': 'file.document'})
#        datas_encoded = base64.encodestring(datas)
#        attach_name = '%s_%s.%s' % (prefix_file_name, file_name, extension)
#        vals_attachment = {'name': attach_name,
#                           'datas': datas_encoded,
#                           'datas_fname': attach_name}
#        attachment_id = attach_obj.create(cr, uid, vals_attachment, context=context)
#        return True

    def check_state_file_document_scheduler(self, cr, uid, domain=None, context=None):
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
        for filedocument in self.browse(cr, uid, ids, context=context):
            self._run(cr, uid, filedocument, context=context)
            if filedocument.direction == 'input':
                filedocument.done()
        return True

    def _run(self, cr, uid, filedocument, context=None):
        filedocument._set_state('running', context=context)

    def done(self, cr, uid, ids, context=None):
        self._set_state(cr, uid, ids, 'done', context=context)

    def _set_state(self, cr, uid, ids, state, context=None):
        for id in ids:
            self.write(cr, uid, id, {'state': state}, context=context)

    def check_state(self, cr, uid, ids, context=None):
        """ Inherit this function in your module """
        return True
