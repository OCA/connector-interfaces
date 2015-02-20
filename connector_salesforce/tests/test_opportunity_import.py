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


class OpportunityImportTest(CommonTest):

    def setUp(self):
        """Setup test using erp as product master"""
        super(opportunityImportTest, self).setUp()
        self.model_name = 'connector.salesforce.opportunity'
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
        response = MagicMock(name='simple_quotation_import')
        response.side_effect = [
            {'records': [{'Id': 'uuid_opportunity_01'}]},
            {'records': [{'Id': 'uuid_opportunity_01'}]},
            fixture.opportunity,
            fixture.account,
            {'records': [{'Id': 'uuid_opportunityline_01'}]},
            fixture.opportunity_line,
            {
                'records': [
                    {'PricebookEntry': {'Product2Id': 'uuid_product_01'}}
                ]
            },
        ]
        with mock_simple_salesforce(response):
            self.backend.import_sf_opportunity()
        imported_id = self.imported_model.search(
            self.cr,
            self.uid,
            [('salesforce_id', '=', 'uuid_opportunity_01'),
             ('backend_id', '=', self.backend.id)]
        )
        self.assertTrue(imported_id)
        self.assertEqual(len(imported_id), 1)
        imported = self.imported_model.browse(
            self.cr,
            self.uid,
            imported_id[0]
        )
        self.assertEqual(imported.origin, 'A won opportunity')
        self.assertEqual(imported.order_policy, 'manual')
        self.assertEqual(imported.currency_id.name, 'EUR')
        self.assertEqual(imported.shop_id.id, 1)
        self.assertEqual(imported.partner_id.name, 'Main name')
        self.assertEqual(imported.partner_invoice_id.name, 'Main name')
        self.assertEqual(imported.partner_shipping_id.name, 'Main name')
        self.assertEqual(imported.partner_id, imported.partner_invoice_id)
        self.assertNotEqual(imported.partner_id, imported.partner_shipping_id)
        self.assertEqual(imported.state, 'draft')
        self.assertEqual(imported.pricelist_id.currency_id.name, 'EUR')
        self.assertEqual(imported.amount_total, 160.0)
        self.assertEqual(imported.invoice_quantity, u'order')
        self.assertEqual(len(imported.order_line), 1)

        order_line = imported.order_line[0]
        self.assertEqual(order_line.product_id, self.product.openerp_id)
        self.assertEqual(order_line.product_uos_qty, 2.0)
        self.assertEqual(order_line.price_unit, 100.0)
        self.assertEqual(order_line.product_uom_qty, 2.0)
        self.assertEqual(order_line.price_subtotal, 160.0)
        self.assertEqual(order_line.discount, 20.0)
        self.assertEqual(order_line.name, 'A sale')
        self.assertEqual(order_line.state, 'draft'),
