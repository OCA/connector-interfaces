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
import os
from .file_connexion import FileConnection

class file_repository(orm.Model):
    _name = "file.repository"
    _description = "File Repository"

    _columns = {
        'name': fields.char('Name', required=True, size=64),
        'location': fields.char('Location', size=200),
        'username': fields.char('User Name', size=64),
        'password': fields.char('Password', size=64),
        'type': fields.selection([('ftp', 'FTP'),
                                  ('sftp', 'SFTP'),
                                  ('filestore', 'Filestore'),
                                  ], 'Type', required=True),
        'port': fields.integer('Port'),
        'task_ids': fields.one2many('repository.task',
                                    'repository_id',
                                    string="Tasks"),
    }

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Repository names must be unique !')
    ]

    def repository_connection(self, cr, uid, id, context=None):
        if isinstance(id, list):
            id=id[0]
        repository = self.browse(cr, uid, id, context=context)
        try:
            return FileConnection(repository.type, repository.location,
                                  repository.username, repository.password,
                                  port=repository.port, allow_dir_creation=True)
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
        'home_folder': fields.char('Home Folder', size=64),
        'file_name': fields.char('File Name', size=64),
        'repository_id': fields.many2one('file.repository',
                                         string="Repository",
                                         required=True,
                                         ondelete="cascade"),
        'direction': fields.selection([('in', 'Import'),
                                       ('out', 'Export')], 'Direction')
    }

    def _check_extension(self, filename):
        (shortname, ftype) = os.path.splitext(filename)
        if not ftype:
            #We do not use osv exception we do not want to have it logged
            raise (_('Please use a file with an extention'))
        return shortname, ftype

    def prepare_buffer_vals(self, cr, uid, task, context=None):
        return {'name': task.name,
                'active': True,
                'repository_id': task.repository_id.id,
                'direction': 'input',
                'task_id': self._name+','+str(task.id),
                }

    def run_import(self, cr, uid, connection, task, context=None):
        buffer_obj = self.pool['file.buffer']
        for file_name in connection.search(task.home_folder, task.file_name):
            file_toimport = connection.get(task.home_folder, file_name)
            datas = file_toimport.read()
            vals = self.prepare_buffer_vals(cr, uid, task, context=context)
            buffer_id = buffer_obj.create(cr, uid, vals, context=context)
            shortname, ftype = self._check_extension(file_name)
            buffer_obj.create_file_buffer_attachment(cr, uid,
                                                     buffer_id,
                                                     datas,
                                                     shortname,
                                                     context=context,
                                                     extension=ftype.replace('.',''))
        return True

    def run(self, cr, uid, ids, context=None):
        """ Execute the repository task.
        For import : - find the files on the repository,
                     - create a file buffer for each found files
                     - attach it the selected file
        """
        repo_obj = self.pool['file.repository']
        for task in self.browse(cr, uid, ids, context=context):
            if not task.active:
                continue
            connection = repo_obj.repository_connection(cr, uid,
                                                        task.repository_id.id,
                                                        context=context)
            #only support the import for now
            if task.direction == 'in':
                self.run_import(cr, uid, connection, task, context=context)
        return True





#from openerp.osv.osv import except_osv
#from base_file_protocole.base_file_protocole import FileConnection
#from tools.translate import _
#from base_external_referentials.external_referentials import REF_VISIBLE_FIELDS

#REF_VISIBLE_FIELDS.update({
#    'SFTP': ['location', 'apiusername', 'apipass'],
#    'FTP': ['location', 'apiusername', 'apipass'],
#})


#class external_referential(orm.Model):
#    _inherit = "external.referential"

    #def external_connection(self, cr, uid, id, debug=False, logger=False, context=None):
    #    if isinstance(id, list):
    #        id=id[0]
    #    referential = self.browse(cr, uid, id, context=context)
    #    try:
    #        return FileConnection(referential.type_id.code, referential.location, referential.apiusername,\
    #                        referential.apipass, port=referential. port, allow_dir_creation = True, \
    #                        home_folder=referential.home_folder)
    #    except Exception, e:
    #        raise except_osv(_("Base File Protocole Connection Error"),
    #                         _("Could not connect to server\nCheck url & user & password.\n %s") % e)

    #_columns={
    #    'port': fields.integer('Port'),
    #    'home_folder': fields.char('Home Folder', size=64),
    #}

    #def _prepare_external_referential_fieldnames(self, cr, uid, context=None):
    #    res = super(external_referential, self)._prepare_external_referential_fieldnames(cr, uid, context=context)
    #    res.append('protocole')
    #    return res
    #
    #def _prepare_external_referential_vals(self, cr, uid, referential, context=None):
    #    res = super(external_referential, self)._prepare_external_referential_vals(cr, uid, referential, context=context)
    #    res['protocole'] = referential.protocole
    #    return res
