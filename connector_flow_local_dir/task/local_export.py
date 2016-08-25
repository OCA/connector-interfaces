# -*- coding: utf-8 -*-
# ©  2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import os
from base64 import b64decode

from openerp import models, api

from openerp.addons.connector_flow.task.abstract_task import AbstractTask
import logging
_logger = logging.getLogger(__name__)


class LocalDirExport(AbstractTask):
    """
    Local Dir Configuration Options:
        - in directory, out directory, backup directory
    """

    def _source_name(self, in_directory, file_name):
        """helper to get the full name"""
        return in_directory + '/' + file_name

    def _create_out_file(self, config, filename, filedata):
        local_dir_config = config['local_dir']
        out_directory = local_dir_config.get('out_directory', '')

        if os.path.exists(self._source_name(out_directory, filename)):
            raise Exception(_('The file %s already exists in the output'
                              'directory') % filename)
        else:
            with open(self._source_name(out_directory, filename), 'w+')\
                    as out_file:
                out_file.write(filedata)
                out_file.close()

    def run(self, config=None, file_id=None, async=True):
        f = self.session.env['impexp.file'].browse(file_id)
        self._create_out_file(config, f.attachment_id.datas_fname,
                              b64decode(f.attachment_id.datas))


class LocalDirExportTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(LocalDirExportTask, self)._get_available_tasks() + [
            ('local_dir_export', 'Local Dir Export')]

    def local_dir_export_class(self):
        return LocalDirExport
