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
import csv
import simplejson
import logging
_logger = logging.getLogger(__name__)


class table_row_import(abstract_task):
    def _row_generator(self, file_data, config=None):
        """Parses a given blob into rows; returns an iterator to rows.
           Has to be implemented in derived classes."""
        raise Exception("Not Implemented")

    def run(self, config=None, file_id=None, async=True, **kwargs):
        if not file_id:
            return

        includes_header = config.get('includes_header', False)

        f = self.session.browse('impexp.file', file_id)
        lineno = 0
        header = None
        rows = self._row_generator(b64decode(f.attachment_id.datas),
                                   config=config)
        for row in rows:
            lineno += 1
            if includes_header and lineno == 1:
                header = row
                continue
            if not row:
                continue
            name = '%s, line %d' % (f.attachment_id.datas_fname, lineno)
            data = row
            if header:
                data = dict(zip(header, data))
            chunk_id = self.session.create('impexp.chunk',
                                           {'name': name,
                                            'data': simplejson.dumps(data),
                                            'file_id': f.id})
            self.run_successor_tasks(chunk_id=chunk_id, async=async, **kwargs)
            if lineno % 1000 == 0:
                _logger.info('Created %d chunks', lineno)

        self.session.write('impexp.file', f.id, {'state': 'done'})


class csv_import(table_row_import):
    """Parses a CSV file and stores the lines as chunks"""

    def _row_generator(self, file_data, config=None):
        encoding = config.get('encoding', 'utf-8')
        data = file_data.decode(encoding)\
                        .encode('utf-8')\
                        .split("\n")
        return csv.reader(data)


class csv_import_task(orm.Model):
    _inherit = 'impexp.task'

    def _get_available_tasks(self, cr, uid, context=None):
        return super(csv_import_task, self) \
            ._get_available_tasks(cr, uid, context=context) \
            + [('csv_import', 'CSV Import')]

    _columns = {
        'task': fields.selection(_get_available_tasks, string='Task',
                                 required=True),
    }

    def csv_import_class(self):
        return csv_import
