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

import time
import logging

from openerp import models, api
from openerp.addons.connector_flow.task.ftp_upload import FtpUpload

_logger = logging.getLogger(__name__)


class ImprovedFtpUpload(FtpUpload):
    def _handle_existing_target(self, ftp_conn, target_name, filedata):
        _logger.info('Skip existing target %s' % target_name)

    def _target_name(self, ftp_conn, upload_directory, filename):
        return "%s/%f_%s" % (upload_directory,
                             time.time(),
                             filename)


class ImprovedFtpUploadTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(ImprovedFtpUploadTask, self)._get_available_tasks() \
            + [('improved_ftp_upload', 'Improved FTP Upload')]

    def improved_ftp_upload_class(self):
        return ImprovedFtpUpload
