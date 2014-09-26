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
import threading
import logging

try:
    import pyodbc
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning('pyodbc not available')

from openerp.addons.connector.unit.backend_adapter import BackendAdapter
_logger = logging.getLogger(__name__)

lock = threading.Lock()
ODBC_MAX_CHUNK = 2000


class ODBCAdapter(BackendAdapter):
    """Base connector ODBC adapter"""
    _cnx = None
    _table_name = None
    # unique identifier of the odbc database
    # multiple column key not identified
    _prefix = None
    _data_set_lookup_disable = False

    def _connect(self):
        ODBCAdapter._cnx = pyodbc.connect(self.backend_record.dsn,
                                          unicode_results=True)

    @property
    def cnx(self):
        with lock:
            if ODBCAdapter._cnx is None:
                self._connect()
            cursor = ODBCAdapter._cnx.cursor()
            # we check if cursor is active, Naive implementation
            try:
                cursor.execute('SELECT 1').fetchone()
            except pyodbc.ProgrammingError:
                self._connect()
            finally:
                cursor.close()
        return ODBCAdapter._cnx

    def _sql_query(self, sql, *args):
        """Execute an SQL query and return pyodbc rows

        :param sql: SQL query
        :type sql: str

        :return: pyodbc rows see https://code.google.com/p/pyodbc/wiki/Rows
        """
        # pyodbc has no context manager
        # see http://code.google.com/p/pyodbc/issues/detail?id=100
        cursor = self.cnx.cursor()
        try:
            if args:
                return cursor.execute(sql, args).fetchall()
            return cursor.execute(sql).fetchall()
        except pyodbc.DatabaseError as exc:
            _logger.error((sql, args))
            _logger.error(repr(exc))
            raise exc
        finally:
            cursor.close()

    def get_unique_key_column(self):
        """Retrun the unique key of a SQL row

        :return: unique key
        :rtype: str
        """
        raise NotImplemented(
            'get_unique_key_column not implemented for %s' % self
        )

    def get_date_columns(self):
        """Define creation and update columns of SQL row

        :return: can return  a tuple (create_date, modify_date) or None
        """
        return None

    def get_sql_conditions(self):
        """ Return where clause + args"""
        return ('', [])

    def adapt_dates_query(self):
        """Adds required SQL to add create_time and modify_time to
        query result row"""
        if not self.get_date_columns():
            return ''
        return (", %s as create_time, %s as modify_time" %
                self.get_date_columns())

    def adapt_dates_filter(self, date):
        """Standardize date columns name

        :param date: tuple of (create_date_name, update_date_name)
        :type date: tuple

        :return: unified date clause
        :rtype: str

        """
        return " create_time > ? or modify_time > ?", [date, date]

    def get_read_sql(self, code_slice):
        """Provides default SQL to read from ODBC data

        :param code_slice: list of external code to read
        :type code_slice: iterable of string
        :return: SQL query
        :rtype: str
        """
        # pyodbc does not support array formatting
        in_format = ', '.join(['?' for c in code_slice])
        sql = "SELECT *%s FROM %s WHERE %s IN (%s)" % (
            self.adapt_dates_query(),
            self._table_name,
            self.get_unique_key_column(),
            in_format
        )
        return sql

    def lookup_data_set(self, data_set, code):
        """ Return a generator of matching data in data_set memoizer

        :param data_set: Memoizer dict
        :type data_set: dict

        :param code: lookup code
        :type code: str

        :return: a generator of matching data in data_set memoizer
        :rtype: generator
        """
        return (x for x in data_set
                if getattr(x, self.get_unique_key_column(), None) == code)

    def read(self, odbc_codes, data_set=None):
        """ Return a generator of data read from ODBC date source

        :odbc_codes: list of code to read
        :type odbc_code: list
        :param data_set: Memoizer dict
        :type data_set: dict

        :return: a generator of data read from ODBC date source
        :rtype: generator
        """
        if not isinstance(odbc_codes, list):
            odbc_codes = [odbc_codes]
        # Optimisation tweak, negotiate database connexion is consumming
        # and not efficient for initial import
        if data_set and not self._data_set_lookup_disable:
            for code in odbc_codes:
                lookup = self.lookup_data_set(data_set, code)
                for row in lookup:
                    yield row
            return

        # SQL server number of remote argument are limited to 2100
        # we slice code in part of 2000
        # Slice code taken from Python Cookbook
        sliced_codes = [odbc_codes[i:i + ODBC_MAX_CHUNK]
                        for i in xrange(0, len(odbc_codes), ODBC_MAX_CHUNK)]
        for code_slice in sliced_codes:
            sql = self.get_read_sql(code_slice)
            for row in self._sql_query(sql, *code_slice):
                yield row

    def get_missing_sql(self, code_slice):
        """Provides default SQL to read ODBC data
        that are not in openerp

        :param code_slice: list of external code to read
        :type code_slice: iterable of string
        :return: SQL query
        :rtype: str
        """
        # pyodbc does not support array formatting
        in_format = ', '.join(['?' for c in code_slice])
        sql = "SELECT %s FROM %s WHERE %s  IN (%s)" % (
            self.get_unique_key_column(),
            self._table_name,
            self.get_unique_key_column(),
            in_format
        )
        return sql

    def missing(self, codes):
        """Get missing records in Odoo for current backend
        :param codes: list of missing codes
        :type codes: list

        :return: list of missing pyodbc rows
                 see https://code.google.com/p/pyodbc/wiki/Row
        """
        # SQL server number of remote argument are limited to 2100
        # we slice code in part of 2000
        # Slice code taken from Python cookbook
        #
        sliced_codes = [codes[i:i + ODBC_MAX_CHUNK]
                        for i in xrange(0, len(codes), ODBC_MAX_CHUNK)]
        res = []
        for code_slice in sliced_codes:
            sql = self.get_missing_sql(code_slice)
            res.extend([x[0] for x in self._sql_query(sql, *code_slice)])
        res = set(res)
        existing = set(codes)
        return list(existing - res)

    def search(self, date=False):
        """Search all data in ODBC backend at lookup date

        :param date: lookup date for data
        :type date: Odoo date string
        :return: a list of odbc code
        :rtype: list
        """
        # Some databases does not suport alias in where clause
        # we have to do a derived table
        # Derived table allow to add global where clause
        # Maybe add a hook get_search_sql but it does not seems
        # really relevent here
        args = []
        filter_where, filter_args = self.get_sql_conditions()
        sql = """SELECT code FROM
                  (SELECT %s AS code %s FROM %s %s) src_table
             """ % (self.get_unique_key_column(),
                    self.adapt_dates_query(),
                    self._table_name,
                    filter_where)
        args += filter_args
        if date and self.get_date_columns():
            date_where, date_args = self.adapt_dates_filter(date)
            args += date_args
            sql += "WHERE %s" % date_where
        res = self._sql_query(sql, *args)
        # we may want to return generator but lsit seems more usable
        return [x[0] for x in res]
