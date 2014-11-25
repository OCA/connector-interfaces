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
from openerp.addons.connector.unit.mapper import mapping, only_create
from ..unit.mapper import ODBCRowImportMapper
from ..backend import odbc_backend
from ..unit.binder import odbc_bound
from ..unit.import_synchronizer import (DirectBatchODBCSynchronizer,
                                        DelayedBatchODBCSynchronizer,
                                        ODBCSynchronizer)
from ..unit.odbc_adapter import ODBCAdapter
from openerp.osv import orm, fields


class test_code_a(orm.Model):
    """Dummy model only used for sychronization tests"""

    _name = "odbc.connector.test.code.a"
    _description = """Dummy model only used for test"""
    _columns = {'code': fields.char('Code', required=True,
                                    select=True),
                'name': fields.char('Name', required=True),
                'active': fields.boolean('Active'),
                'desc': fields.text('Desc.'),
                'test_date': fields.date('Date'),
                'test_datetime': fields.datetime('Date time'),
                }

    _defaults = {'active': True}


@odbc_bound
class odbc_code_a(orm.Model):
    """Test model"""
    _inherit = "odbc.string.server.binding"
    _inherits = {'odbc.connector.test.code.a': 'openerp_id'}
    _name = "odbc.data.connector.test.code.a"
    _description = """external table into odbc.connector.test.code.a"""

    _columns = {'openerp_id': fields.many2one('odbc.connector.test.code.a',
                                              'Test code',
                                              required=True,
                                              ondelete='restrict')}

    _sql_contraints = [
        ('odbc_uniq', 'unique(backend_id, odbc_code)',
         'A test code with same ODBC data code already exists')
    ]


@odbc_backend
class TestCodeODBCSynchronizer(ODBCSynchronizer):
    _model_name = "odbc.data.connector.test.code.a"


@odbc_backend
class TestCodeDirectBatchODBCSynchronizer(DirectBatchODBCSynchronizer):
    _model_name = "odbc.data.connector.test.code.a"


@odbc_backend
class TestCodeDelayedBatchODBCSynchronizer(DelayedBatchODBCSynchronizer):
    _model_name = "odbc.data.connector.test.code.a"


@odbc_backend
class CustomerODBCObjectAdapter(ODBCAdapter):
    _table_name = "mega_code_table"
    _model_name = "odbc.data.connector.test.code.a"

    def get_date_columns(self):
        return ("mg_createTime", "mg_modifyTime")

    def get_unique_key_column(self):
        return "mg_code"

    def get_sql_conditions(self, *args):
        return "WHERE status = ?", ['Active']


@odbc_backend
class CustomerMapper(ODBCRowImportMapper):
    _model_name = "odbc.data.connector.test.code.a"
    direct = [('mg_name', 'name'),
              ('mg_code', 'code'),
              ('mg_desc', 'desc')]

    @only_create
    @mapping
    def odbc_code(self, record):
        return {'odbc_code': record.mg_code}

    @only_create
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @only_create
    @mapping
    def date_datetime(self, record):
        # odbc return real date datetime object
        return {'test_date': str(record.x_date),
                'test_datetime': str(record.x_datetime)}
