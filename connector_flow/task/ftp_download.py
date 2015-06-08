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

from openerp import models, api

from .abstract_task import AbstractTask
import ftputil
import ftputil.session
import logging
_logger = logging.getLogger(__name__)


class FtpDownload(AbstractTask):
    """FTP Configuration options:
     - host, user, password, port
     - download_directory:  directory on the FTP server where files are
                            downloaded from
     - move_directory:  If present, files will be moved to this directory
                        on the FTP server after download.
     - delete_files:  If true, files will be deleted on the FTP server
                      after download.
    """

    def _handle_new_source(self, ftp_conn, download_directory, file_name,
                           move_directory):
        """open and read given file into create_file method,
           move file if move_directory is given"""
        with ftp_conn.open(self._source_name(download_directory, file_name),
                           "rb") as fileobj:
            data = fileobj.read()
        return self.create_file(file_name, data)

    def _source_name(self, download_directory, file_name):
        """helper to get the full name"""
        return download_directory + '/' + file_name

    def _move_file(self, ftp_conn, source, target):
        """Moves a file on the FTP server"""
        _logger.info('Moving file %s %s' % (source, target))
        ftp_conn.rename(source, target)

    def _delete_file(self, ftp_conn, source):
        """Deletes a file from the FTP server"""
        _logger.info('Deleting file %s' % source)
        ftp_conn.remove(source)

    def run(self, config=None, async=True):
        ftp_config = config['ftp']
        download_directory = ftp_config.get('download_directory', '')
        move_directory = ftp_config.get('move_directory', '')
        port_session_factory = ftputil.session.session_factory(
            port=int(ftp_config.get('port', 21)))
        with ftputil.FTPHost(ftp_config['host'], ftp_config['user'],
                             ftp_config['password'],
                             session_factory=port_session_factory) as ftp_conn:

            file_list = ftp_conn.listdir(download_directory)
            downloaded_files = []
            for ftpfile in file_list:
                if ftp_conn.path.isfile(self._source_name(download_directory,
                                                          ftpfile)):
                    file_id = self._handle_new_source(ftp_conn,
                                                      download_directory,
                                                      ftpfile,
                                                      move_directory)
                    self.run_successor_tasks(file_id=file_id, async=async)
                    downloaded_files.append(ftpfile)

            # Move/delete files only after all files have been processed.
            if ftp_config.get('delete_files'):
                for ftpfile in downloaded_files:
                    self._delete_file(ftp_conn,
                                      self._source_name(download_directory,
                                                        ftpfile))
            elif move_directory:
                if not ftp_conn.path.exists(move_directory):
                    ftp_conn.mkdir(move_directory)
                for ftpfile in downloaded_files:
                    self._move_file(
                        ftp_conn,
                        self._source_name(download_directory, ftpfile),
                        self._source_name(move_directory, ftpfile))


class FtpDownloadTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(FtpDownloadTask, self)._get_available_tasks() + [
            ('ftp_download', 'FTP Download')]

    def ftp_download_class(self):
        return FtpDownload
