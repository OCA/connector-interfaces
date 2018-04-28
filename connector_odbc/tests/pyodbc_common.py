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
from mock import MagicMock
from .sql_data import sql_data


class CursorMock(MagicMock):
    """We mock cursor object that has a special structure"""
    def execute(self, sql, *args, **kwargs):
        self.sql = sql
        self.param = args
        return self

    def fetchall(self, *args, **kwargs):
        sql = self.sql.replace("\n", '').replace(' ', '')
        key = (sql, self.param[0])
        assert key in sql_data, "Generated SQL seems incorrect"
        return sql_data[key]


def pyodbc_mock(*args, **kwargs):
    # pyodbc has no context manager
    # see http://code.google.com/p/pyodbc/issues/detail?id=100
    cnx_mock = MagicMock(spec=['cursor'], name="pyodbc.totoconnect")
    cursor_mock = CursorMock(spec=['execute', 'fetchall', 'fetchone', 'close'],
                             name="pyodbc.cnx.cursor")
    cnx_mock.cursor.return_value = cursor_mock
    return cnx_mock
