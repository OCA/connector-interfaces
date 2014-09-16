# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
import openerp.tests.common as test_common


class ConfiguratorTester(test_common.TransactionCase):

    def test_import_configurator(self):
        """Test the creation of a register with configurator"""
        backend_model = self.registry('connector.odbc.data.server.backend')
        configurator_model = self.registry('connector.odbc.import.configurator')
        b_id = backend_model.create(
            self.cr,
            self.uid,
            {'name': 'Test ODBC connect',
             'version': '1.0',
             'dsn': 'Dummy'}
        )

        model_id = self.registry('ir.model').search(
            self.cr,
            self.uid,
            [('model', '=', 'odbc.data.connector.test.code.a')],
        )

        self.assertTrue(model_id)
        c_id = configurator_model.create(
            self.cr,
            self.uid,
            {
                'backend_id': b_id,
                'model_id': model_id[0],
                'priority': 3,
            }
        )
        configurator = configurator_model.browse(
            self.cr,
            self.uid,
            c_id
        )
        configurator.create_register()
        backend = backend_model.browse(self.cr, self.uid, b_id)
        self.assertTrue(backend.import_register_ids)
        reg = backend._get_register('odbc.data.connector.test.code.a')
        self.assertEqual(reg.model_id.model, 'odbc.data.connector.test.code.a')
        self.assertEqual(reg.backend_id.id, backend.id)
        self.assertEqual(reg.sequence, 3)

    def test_fields_view_get(self):
        backend_model = self.registry('connector.odbc.data.server.backend')
        configurator_model = self.registry('connector.odbc.import.configurator')

        b_id = backend_model.create(
            self.cr,
            self.uid,
            {'name': 'Test ODBC connect',
             'version': '1.0',
             'dsn': 'Dummy'}
        )
        context = {'active_id': b_id}
        configurator_model.fields_view_get(self.cr, self.uid, view_type='form', context=context)
