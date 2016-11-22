# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2015 Camptocamp SA
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
from .common import CommonTest, mock_simple_salesforce
from . import fixture


class PriceBookImportTest(CommonTest):

    def setUp(self):
        """Setup test using erp export by default"""
        super(PriceBookImportTest, self).setUp()
        self.model_name = 'connector.salesforce.pricebook.entry'
        self.imported_model = self.registry(self.model_name)
        self.conn_env = self.get_connector_env(self.model_name)
        prod_id = self.registry('connector.salesforce.product').create(
            self.cr,
            self.uid,
            {
                'salesforce_id': 'uuid_product_01',
                'name': 'Product exported on SF',
                'sale_ok': True,
                'list_price': 0.0,
                'backend_id': self.backend.id,
            }
        )
        self.product = self.registry('connector.salesforce.product').browse(
            self.cr,
            self.uid,
            prod_id
        )

    def test_simple_import(self):
        pl_version = self.get_euro_pricelist_version()
        self.registry('connector.salesforce.pricebook.entry.mapping').create(
            self.cr,
            self.uid,
            {
                'backend_id': self.backend.id,
                'currency_id': pl_version.pricelist_id.currency_id.id,
                'pricelist_version_id': pl_version.id,
            }
        )
        response = MagicMock(name='simple_pricebookentry_import')
        response.side_effect = [
            {'records': [{'Id': 'uuid_pricebookentry_01'}]},
            {'records': [{'dummy': 'dummy'}]},
            fixture.price_book_entry,
        ]
        with mock_simple_salesforce(response):
            self.backend.import_sf_entry()
        imported_id = self.imported_model.search(
            self.cr,
            self.uid,
            [('salesforce_id', '=', 'uuid_pricebookentry_01'),
             ('backend_id', '=', self.backend.id)]
        )
        self.assertTrue(imported_id)
        self.assertEqual(len(imported_id), 1)
        imported = self.imported_model.browse(
            self.cr,
            self.uid,
            imported_id[0]
        )
        self.assertEqual(imported.price_version_id, pl_version)
        self.assertEqual(imported.price_surcharge, 200.00)
        self.assertEqual(imported.product_id, self.product.openerp_id)
