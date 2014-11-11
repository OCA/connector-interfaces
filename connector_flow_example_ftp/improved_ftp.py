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
from openerp.addons.connector_flow.task.ftp_upload import ftp_upload
import time
import logging
_logger = logging.getLogger(__name__)


class improved_ftp_upload(ftp_upload):
    def _handle_existing_target(self, ftp_conn, target_name, filedata):
        _logger.info('Skip existing target %s' % target_name)

    def _target_name(self, ftp_conn, upload_directory, filename):
        return "%s/%f_%s" % (upload_directory,
                             time.time(),
                             filename)


class improved_ftp_upload_task(orm.Model):
    _inherit = 'impexp.task'

    def _get_available_tasks(self, cr, uid, context=None):
        return super(improved_ftp_upload_task, self) \
            ._get_available_tasks(cr, uid, context=context) \
            + [('improved_ftp_upload', 'Improved FTP Upload')]

    _columns = {
        'task': fields.selection(_get_available_tasks, string='Task',
                                 required=True),
    }

    def improved_ftp_upload_class(self):
        return improved_ftp_upload
