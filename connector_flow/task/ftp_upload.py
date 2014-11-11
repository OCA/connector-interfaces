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
from .abstract_task import abstract_task
from base64 import b64decode
import ftputil
import ftputil.session
import logging
_logger = logging.getLogger(__name__)


class ftp_upload(abstract_task):
    """FTP Configuration options:
     - host, user, password, port
     - upload_directory:  directory on the FTP server where files are
                          uploaded to
    """

    def _handle_existing_target(self, ftp_conn, target_name, filedata):
        raise Exception("%s already exists" % target_name)

    def _handle_new_target(self, ftp_conn, target_name, filedata):
        with ftp_conn.open(target_name, mode='wb') as fileobj:
            fileobj.write(filedata)
            _logger.info('wrote %s, size %d', target_name, len(filedata))

    def _target_name(self, ftp_conn, upload_directory, filename):
        return upload_directory + '/' + filename

    def _upload_file(self, config, filename, filedata):
        ftp_config = config['ftp']
        upload_directory = ftp_config.get('upload_directory', '')
        port_session_factory = ftputil.session.session_factory(
            port=int(ftp_config.get('port', 21))
            )
        with ftputil.FTPHost(ftp_config['host'], ftp_config['user'],
                             ftp_config['password'],
                             session_factory=port_session_factory) as ftp_conn:
            target_name = self._target_name(ftp_conn,
                                            upload_directory,
                                            filename)
            if ftp_conn.path.isfile(target_name):
                self._handle_existing_target(ftp_conn, target_name, filedata)
            else:
                self._handle_new_target(ftp_conn, target_name, filedata)

    def run(self, config=None, file_id=None, async=True):
        f = self.session.pool.get('impexp.file') \
                .browse(self.session.cr, self.session.uid, file_id)
        self._upload_file(config, f.attachment_id.datas_fname,
                          b64decode(f.attachment_id.datas))


class ftp_upload_task(orm.Model):
    _inherit = 'impexp.task'

    def _get_available_tasks(self, cr, uid, context=None):
        return super(ftp_upload_task, self) \
            ._get_available_tasks(cr, uid, context=context) \
            + [('ftp_upload', 'FTP Upload')]

    _columns = {
        'task': fields.selection(_get_available_tasks, string='Task',
                                 required=True),
    }

    def ftp_upload_class(self):
        return ftp_upload
