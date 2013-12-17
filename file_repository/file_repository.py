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
from openerp.osv.osv import except_osv
from tools.translate import _
from .file_connexion import FileConnection
from datetime import datetime
import os
import base64
import logging

_logger = logging.getLogger(__name__)


class file_repository(orm.Model):
    _name = "file.repository"
    _description = "File Repository"

    _columns = {
        'name': fields.char('Name', required=True, size=64),
        'location': fields.char('Location', size=200),
        'username': fields.char('User Name', size=64),
        'password': fields.char('Password', size=64),
        'home_folder': fields.char(
            'Home folder',
            size=64,
            help="Absolute path in the repository",),
        'type': fields.selection(
            [('ftp', 'FTP'),
             ('sftp', 'SFTP'),
             ('filestore', 'Filestore'),],
            'Type',
            required=True),
        'port': fields.integer('Port'),
        'task_ids': fields.one2many(
            'repository.task',
            'repository_id',
            string="Tasks"),
    }

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Repository names must be unique !')
    ]

    def repository_connection(self, cr, uid, id, context=None):
        if isinstance(id, list):
            id = id[0]
        repository = self.browse(cr, uid, id, context=context)
        try:
            return FileConnection(repository.type, repository.location,
                                  repository.username, repository.password,
                                  port=repository.port,
                                  allow_dir_creation=True,
                                  home_folder=repository.home_folder)
        except Exception, e:
            raise except_osv(_("Repository Connection Error"),
                             _("Could not connect to repository\n"
                               "Check url, user & password.\n %s") % e)


class repository_task(orm.Model):
    _name = 'repository.task'
    _description = 'Repository Task'
    _inherit = 'abstrack.task'

    _columns = {
        'name': fields.char('Name', size=64),
        'file_name': fields.char(
            'File Name',
            size=64,
            help="If the file name change, set here the common part "
                 "of this name (prefix or suffix)"),
        'repository_id': fields.many2one(
            'file.repository',
            string="Repository",
            required=True,
            ondelete="cascade"),
        'direction': fields.selection(
            [('in', 'Import'),
             ('out', 'Export')],
            'Direction',
            required=True),
        'folder': fields.char(
            'Folder',
            size=64,
            help="Folder where the file is on the repository "
                 "(relative path to 'Home folder' repository field )"),
        'archive_folder': fields.char(
            'Archive Folder',
            size=64,
            help="The file will be moved to this folder after import"),
    }

    def prepare_document_vals(self, cr, uid, task, file_name, datas,
                              context=None):
        return {'name': file_name,
                'active': True,
                'repository_id': task.repository_id.id,
                'direction': 'input',
                'task_id': self._name+','+str(task.id),
                'datas': datas,
                'datas_fname': file_name
                }

    def import_one_document(self, cr, uid, connection, task, file_name,
                            folder_path, context=None):
        document_obj = self.pool['file.document']
        file_toimport = connection.get(folder_path, file_name)
        datas = file_toimport.read()
        datas_encoded = base64.encodestring(datas)
        vals = self.prepare_document_vals(cr, uid, task, file_name,
                                          datas_encoded, context=context)
        document_obj.create(cr, uid, vals, context=context)
        if task.archive_folder:
            connection.move(folder_path, task.archive_folder, file_name)
        return True

    def run_import(self, cr, uid, connection, task, context=None):
        document_obj = self.pool['file.document']
        document_ids = document_obj.search(
            cr, uid, [('task_id', '=', self._name+','+str(task.id))],
            context=context)
        file_names = document_obj.read(cr, uid, document_ids, ['name'],
                                       context=context)
        folder_path = get_full_path(task.repository_id.home_folder, task.folder)
        for file_name in connection.search(folder_path, task.file_name):
            if not file_name in file_names:
                self.import_one_document(cr, uid, connection, task, file_name,
                                         folder_path, context=context)
        return True

    def run(self, cr, uid, ids, context=None):
        """ Execute the repository task.
        For import : - find the files on the repository,
                     - create a file document for each found files
                     - attach it the selected file
        """
        vals = {'last_exe_date': datetime.now()}
        self.write(cr, uid, ids, vals, context=context)
        repo_obj = self.pool['file.repository']
        for task in self.browse(cr, uid, ids, context=context):
            if not task.active:
                continue
            connection = repo_obj.repository_connection(cr, uid,
                                                        task.repository_id.id,
                                                        context=context)
            #only support the import for now
            if task.direction == 'in':
                _logger.info('Start to run import task %s'%task.name)
                self.run_import(cr, uid, connection, task, context=context)
        return True


def get_full_path(path1, path2):
    path1 = path1 or ''
    path2 = path2 or ''
    return os.path.join(path1, path2)
