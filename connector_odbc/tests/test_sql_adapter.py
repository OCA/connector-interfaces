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
from mock import patch
from . import odbc_test_common
from . import pyodbc_common
from ..unit.odbc_adapter import ODBCAdapter


class test_sql_adapter(odbc_test_common.ODBCBaseTestClass):

    def setUp(self):
        super(test_sql_adapter, self).setUp()
        self.target_model = self.registry('odbc.connector.test.code.a')

    @patch('pyodbc.connect', pyodbc_common.pyodbc_mock)
    def test_00_test_sql_adapter_search(self):
        """ We test there is no regression in code that search external DB,
        This is a simple test that ensure Generated SQL is matched in a collection"""
        adapter = self.env.get_connector_unit(ODBCAdapter)
        self.assertEqual(adapter._table_name, 'mega_code_table')
        search_res = adapter.search()
        self.assertEqual(search_res, ['1', '2', '3', '4', '5'])

    @patch('pyodbc.connect', pyodbc_common.pyodbc_mock)
    def test_01_test_sql_adapter_read(self):
        """ We test there is no regression in code that search external DB,
        This is a simple test that ensure Generated SQL is matched in a collection.
        We also walidate memoizer"""
        adapter = self.env.get_connector_unit(ODBCAdapter)
        self.assertEqual(adapter._table_name, 'mega_code_table')
        read_res = adapter.read(['2', '1', '3', '4', '5'])
        data = [x for x in read_res]  # read_res is a generator
        # I test return is sorted and correct
        self.assertTrue(data[1].mg_code == '1', msg="Incorrect order")
        # I test len of recordset
        self.assertEqual(len(data), 5,
                         msg="Recordset has not the correct items number")
        read_res_optimized = adapter.read(['2', '1', '3', '4', '5'], data_set=data)
        optimized_data = [x for x in read_res_optimized]
        # I test return is sorted and correct
        self.assertTrue(optimized_data[1].mg_code == '1', msg="Incorrect optimized order")
        # I test len of recordset
        self.assertEqual(len(optimized_data), 5)
