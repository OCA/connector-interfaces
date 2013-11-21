# -*- coding: utf-8 -*-
###############################################################################
#
#   file_repository for OpenERP
#   Authors: Sebastien Beau <sebastien.beau@akretion.com>
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
from openerp.addons.file_autotask_rel.file_document import add_task
from tempfile import TemporaryFile
import base64

add_task('repository.task')


class FileDocument(orm.Model):
    _inherit = "file.document"

    _columns = {
        'repository_id': fields.many2one(
            'file.repository',
            'File Repository'),
    }

    def export_file_document(self, cr, uid, connection, file_doc,
                             context=None):
        outfile = TemporaryFile('w+b')
        decoded_datas = base64.decodestring(file_doc.datas)
        outfile.write(decoded_datas)
        outfile.seek(0)
        connection.send(file_doc.task_id.folder,
                        file_doc.datas_fname, outfile)
        return outfile

    def _run(self, cr, uid, file_doc, context=None):
        super(FileDocument, self)._run(cr, uid, file_doc, context=context)
        repo_obj = self.pool['file.repository']
        if file_doc.direction == 'output' and file_doc.active == True:
            connection = repo_obj.repository_connection(
                cr, uid, file_doc.repository_id.id, context=context)
            self.export_file_document(cr, uid, connection, file_doc,
                                      context=context)
            file_doc.done()
