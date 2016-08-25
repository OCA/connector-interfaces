# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# ©  2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import os
from openerp import models, api

from openerp.addons.connector_flow.task.abstract_task import AbstractTask
import logging
_logger = logging.getLogger(__name__)


class LocalDirImport(AbstractTask):
    """
    Local Dir Configuration Options:
        - in directory, out directory, backup directory
    """

    def _handle_new_source(self, in_directory, in_file):
        """open and read given file into create_file method,
           """
        with open(self._source_name(in_directory, in_file)) as fileobj:
            data = fileobj.read()

        return self.create_file(in_file, data)

    def _source_name(self, in_directory, file_name):
        """helper to get the full name"""
        return in_directory + '/' + file_name

    def _move_file(self, source, target):
        """Moves a file on the directory"""
        _logger.info('Moving file %s %s' % (source, target))
        os.rename(source, target)

    def _delete_file(self, source):
        """Deletes a file from the directory"""
        _logger.info('Deleting file %s' % source)
        os.remove(source)

    def _get_in_files(self, in_directory):
        return [f for f in os.listdir(in_directory)]

    def run(self, config=None, async=True):
        local_dir_config = config['local_dir']
        in_directory = local_dir_config.get('in_directory', '')
        backup_directory = local_dir_config.get('backup_directory', '')

        in_files = self._get_in_files(in_directory)

        for in_file in in_files:
            file_id = self._handle_new_source(in_directory, in_file)
            if file_id:
                self.run_successor_tasks(file_id=file_id, async=async)
                if local_dir_config['delete_files']:
                    self._delete_file(self._source_name(in_directory, in_file))
                elif backup_directory:
                    if not os.path.exists(backup_directory):
                        os.mkdir(backup_directory)
                    self._move_file(self._source_name(in_directory, in_file),
                                    self._source_name(backup_directory,
                                                      in_file))
                    # Avoid downloaded file not be saved if an error occur
                    # in the same transaction
                    self.session.commit()


class LocalDirImportTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(LocalDirImportTask, self)._get_available_tasks() + [
            ('local_dir_import', 'Local Dir Import')]

    def local_dir_import_class(self):
        return LocalDirImport
