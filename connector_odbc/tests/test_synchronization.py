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
import time
import psycopg2

from openerp.tools.misc import mute_logger
from . import odbc_test_common
from .adapter_data import simulated_mega_table


class test_direct_synchro(odbc_test_common.ODBCBaseTestClass):

    def setUp(self):
        super(test_direct_synchro, self).setUp()
        self.connector_model = self.registry('odbc.data.connector.test.code.a')
        self.target_model = self.registry('odbc.connector.test.code.a')
        irmodel_model = self.registry('ir.model')
        model = irmodel_model.search(
            self.cr, self.uid,
            [('model', '=', self.connector_model._name)]
        )
        self.assertTrue(model, msg='No model found')
        register_model = self.registry('connector.odbc.import.register')
        register_model.create(
            self.cr,
            self.uid,
            {'model_id': model[0],
             'backend_id': self.backend.id,
             'sequence': 1}
        )

    def test_02_first_direct_import(self):
        """Test first import"""
        # You can not mock instance of Adapter
        # As Synchronizer has a factory for adapter
        cr, uid = self.cr, self.uid
        existing = self.target_model.search(cr, uid, [])
        self.assertEqual(existing, [])
        with odbc_test_common.mock_adapter('mega_code_table', 'mg_code',
                                           simulated_mega_table):
            self.backend.direct_import(['odbc.data.connector.test.code.a'],
                                       full=True)
        codes = ['1', '2', '3', '4', '5']
        # we validate relation Model between backend, external data and openerp
        imported = self.connector_model.search(
            cr, uid, [('odbc_code', 'in', codes),
                      ('backend_id', '=', self.backend.id)]
        )
        self.assertEqual(len(imported), 5,
                         "Did not find 5 relations in OpenERP")
        # we validate openerp Model were correctly inserted and transformed
        openerp_ids = self.target_model.search(cr, uid,
                                               [('code', 'in', codes)])
        self.assertEqual(len(openerp_ids), 5, "Did not find 5 rows in OpenERP")
        br_to_validate = self.target_model.browse(cr, uid, openerp_ids[0])

        self.assertEqual(
            br_to_validate.name,
            'name 1', 'invalid name'
        )
        self.assertEqual(
            br_to_validate.code,
            '1',
            'invalid code'
        )
        self.assertEqual(
            br_to_validate.test_date,
            '2010-01-01',
            'invalide date'
        )
        self.assertEqual(
            br_to_validate.test_datetime,
            '2011-01-01 00:00:00',
            'invalide date'
        )
        # we rebrowse refrech does not seems to work
        backend = self.backend_model.browse(
            cr, uid, self.backend.id)
        back_date = backend._get_register(
            self.connector_model._name).last_import_date

        self.assertTrue(back_date, msg="backend date not set")

    def test_03_update_import(self):
        """Test second pass of import. Row with code 1 has been updated"""
        # I simulate the last import date
        cr, uid = self.cr, self.uid
        register = self.backend._get_register(self.connector_model._name)
        register.write({'last_import_date': "2012-06-01 00:00:00"})
        cr.execute(
            'Select MAX(sync_date) FROM odbc_data_connector_test_code_a'
        )
        highest_update_date = cr.fetchone()[0]
        time.sleep(1)
        with odbc_test_common.mock_adapter('mega_code_table', 'mg_code',
                                           simulated_mega_table):
            self.backend.direct_import(
                ['odbc.data.connector.test.code.a'],
                full=False
            )
        updated_ids = self.connector_model.search(
            cr, uid,
            [('sync_date', '>', highest_update_date)]
        )
        self.assertEqual(
            len(updated_ids), 1,
            msg="Wrong number of update"
        )
        br_to_validate = self.connector_model.browse(cr, uid, updated_ids[0])
        self.assertEqual(
            br_to_validate.desc,
            'comment updated',
            msg="Attribute was not updated"
        )

    def test_04_correct_delete_row(self):
        """I test deletion of data in OpenERP in a correct manner"""
        cr, uid = self.cr, self.uid
        to_del_ids = self.connector_model.search(cr, uid,
                                                 [('odbc_code', '=', '4')])
        self.assertTrue(to_del_ids)
        to_del_br = self.connector_model.browse(cr, uid, to_del_ids[0])
        related = to_del_br.openerp_id
        # we delete the correct way by supressing binding then related
        self.connector_model.unlink(cr, uid, to_del_br.id)
        self.assertFalse(self.connector_model.search(
            cr, uid,
            [('id', '=', to_del_ids[0])])
        )
        self.assertTrue(self.target_model.search(
            cr, uid,
            [('id', '=', related.id)])
        )
        self.assertTrue(self.target_model.unlink(cr, uid, related.id))

    def test_05_update_delete(self):
        """Test second pass of import. Row with code 3 has been deleted
        in external data source"""
        cr, uid = self.cr, self.uid
        # code 3  will be imported
        # and when checking missing
        # we mock 3 was deleted from ODBC data source
        register = self.backend._get_register(self.connector_model._name)
        register.write({'last_import_date': "2012-06-03 00:00:00"})
        with odbc_test_common.mock_adapter('mega_code_table', 'mg_code',
                                           simulated_mega_table):
            self.backend.direct_import(
                ['odbc.data.connector.test.code.a'],
                full=False
            )
        deactivated = self.target_model.search(
            cr, uid, [('code', '=', '3'),
                      ('active', '=', False)]
        )
        self.assertTrue(
            deactivated,
            msg="Nothing was deactivated"
        )
        self.assertEqual(
            len(deactivated),
            1,
            msg="Wrong number of deactivations"
        )
        deact_br = self.connector_model.browse(cr, uid, deactivated[0])
        self.assertEqual(deact_br.code, '3')

    def test_06_incorrect_delete_row(self):
        """Test that we can not delete row linked to bindings"""
        cr, uid = self.cr, self.uid
        to_del_ids = self.connector_model.search(
            cr, uid,
            [('odbc_code', '=', '5')]
        )
        self.assertTrue(to_del_ids)
        # it should fail
        with mute_logger('openerp.sql_db'):
            with self.assertRaises(psycopg2.IntegrityError):
                self.target_model.unlink(cr, uid, to_del_ids[0])
        cr.rollback()
