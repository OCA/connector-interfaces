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

class ContactImportTest(CommonTest):

    def setUp(self):
        super(ContactImportTest, self).setUp()
        self.account_model_name = 'connector.salesforce.contact'
        self.imported_model = self.registry(self.account_model_name)
        self.conn_env = self.get_connector_env(self.account_model_name)


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
        response = MagicMock(name='simple_contact_import')
        response.side_effect = [
            {'records': [{'Id': 'uuid_contact_01'}]},
            fixture.contact,
            fixture.account,
        ]
        with mock_simple_salesforce(response):
            self.backend.import_sf_contact()

        imported_id = self.imported_model.search(
            self.cr,
            self.uid,
            [('salesforce_id', '=', 'uuid_contact_01'),
             ('backend_id', '=', self.backend.id)]
        )
        self.assertTrue(imported_id)
        self.assertEqual(len(imported_id), 1)
        imported = self.imported_model.browse(
            self.cr,
            self.uid,
            imported_id[0]
        )
        self.assertEqual(imported.name, 'Contact lastname Contact firstname')
        self.assertEqual(imported.street, 'Contact street')
        self.assertEqual(imported.city, 'Contact city')
        self.assertEqual(imported.fax, '+41 21 619 10 10')
        self.assertEqual(imported.phone, '+41 21 619 10 12')
        self.assertEqual(imported.sf_assistant_phone, '+41 21 619 10 15')
        self.assertEqual(imported.sf_other_phone, '+41 21 619 10 13')
        self.assertEqual(imported.mobile, '+41 21 619 10 14')
        self.assertEqual(imported.phone, '+41 21 619 10 12')
        self.assertEqual(imported.email, 'contact@mail.ch')
        self.assertEqual(imported.zip, 'Contact zip')
        self.assertEqual(imported.state_id.name, 'Contact state')
        self.assertEqual(imported.country_id.code, 'CH')
        self.assertFalse(imported.is_company)
        self.assertEqual(imported.parent_id.name, 'Main name')
