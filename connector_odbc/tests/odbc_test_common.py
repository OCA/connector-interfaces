# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
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
import logging
from contextlib import contextmanager

import openerp.tests.common as test_common
from mock import MagicMock, patch
from ..unit import import_synchronizer

_logger = logging.getLogger(__name__)


class ODBCBaseTestClass(test_common.SingleTransactionCase):
    def _get_backend(self):
        b_ids = self.backend_model.search(self.cr, self.uid,
                                          [('name', '=', 'Test ODBC connect')])
        if b_ids:
            b_id = b_ids[0]
        else:
            b_id = self.backend_model.create(self.cr, self.uid,
                                             {'name': 'Test ODBC connect',
                                              'version': '1.0',
                                              'dsn': 'Dummy'})
        return self.backend_model.browse(self.cr, self.uid, b_id)

    def setUp(self):
        super(ODBCBaseTestClass, self).setUp()
        self.backend_model = self.registry(
            'connector.odbc.data.server.backend'
        )
        self.backend = self._get_backend()
        self.env = self._get_backend().get_environment(
            'odbc.data.connector.test.code.a'
        )
        # We do not want to commit during test
        import_synchronizer.FORCE_COMMIT = False

    def tearDown(self):
        super(ODBCBaseTestClass, self).tearDown()
        # We enable commit after tests
        import_synchronizer.FORCE_COMMIT = True


class SQLAdapterMock(MagicMock):
    """Mock SQL adapter"""

    _table_name = None
    _simulated_data = None

    def search(self,  **kwargs):
        key = (self._table_name,
               'search',
               tuple(kwargs.items()) if kwargs else None)
        data = self._simulated_data[key]
        _logger.debug(data)
        return data

    def missing(self, codes):
        key = (self._table_name,
               'missing',
               tuple(codes))
        data = self._simulated_data[key]
        _logger.debug(data)
        return data

    def read(self, codes, data_set=None):
        if data_set:
            for code in codes:
                tmp = (x for x in data_set
                       if getattr(x, self._code_column, None) == code)
                for row in tmp:
                    yield row
            return

        key = (self._table_name,
               'read',
               tuple(codes))
        data = self._simulated_data[key]
        _logger.debug(data)
        for row in data:
            yield row


@contextmanager
def mock_adapter(table_name, code_column, simulated_data):
    """Mock adapter context manager receive external
    system table and mocked recoreds in entry"""
    cl = "openerp.addons.connector.unit.synchronizer.Synchronizer.backend_adapter"  # noqa
    mock = SQLAdapterMock(name="SQLAdapterMock_%s" % table_name)
    with patch(cl, mock) as adapter:
        adapter._table_name = table_name
        adapter._code_column = code_column
        adapter._simulated_data = simulated_data
        _logger.debug(adapter.call_args_list)
        yield
