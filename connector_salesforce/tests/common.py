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
from contextlib import nested, contextmanager
from mock import patch, MagicMock

import openerp.tests.common as test_common

SF_SPECS = ['query_all', 'delete', 'get', 'updated',
            'deleted', 'update', 'create', 'upsert']


class CommonTest(test_common.TransactionCase):

    def _get_backend(self):
        """Provide a fixture backend record for the test"""
        backend_model = self.registry('connector.salesforce.backend')
        b_ids = backend_model.search(
            self.cr, self.uid,
            [('name', '=', 'Salesforce Backend Test')]
        )
        if b_ids:
            b_id = b_ids[0]
        else:
            b_id = backend_model.create(
                self.cr, self.uid,
                {'name': 'Salesforce Backend Test',
                 'version': '15',
                 'url': 'Dummy',
                 'authentication_method': 'oauth2',
                 'consumer_secret': 'Dummy',
                 'callback_url': 'httpd://dummy.dummy',
                 'consumer_code': 'Dummy',
                 'consumer_token': 'Dummy',
                 'consumer_key': 'Dummy',
                 'sf_shop_id': 1,
                 'consumer_refresh_token': 'Dummy'}
            )
        return backend_model.browse(self.cr, self.uid, b_id)

    def get_connector_env(self, model_name):
        self.assertTrue(self.backend)
        return self.backend.get_connector_environment(model_name)

    def setUp(self):
        super(CommonTest, self).setUp()
        self.backend = self._get_backend()

    def get_euro_pricelist_version(self):
        pl_version_id = self.registry('product.pricelist.version').search(
            self.cr,
            self.uid,
            [('pricelist_id.currency_id.name', '=', 'EUR'),
             ('pricelist_id.type', '=', 'sale')]
        )
        self.assertTrue(pl_version_id)
        return self.registry('product.pricelist.version').browse(
            self.cr,
            self.uid,
            pl_version_id[0]
        )


@contextmanager
def mock_simple_salesforce(response_mock):
    """Context manager that will mock the request object used
    to talk with SalesForce

    :param response_mock: A response mock that will be used as
                          the result of a Salesforce interogation
    :type response_mock: :py:class:`mock.MagicMock`

    :yield: current execution stack
    """

    def _get_response(*args, **kwargs):
        return response_mock

    for fun in SF_SPECS:
        setattr(response_mock, fun, response_mock)
    klass = ('openerp.addons.connector_salesforce.unit'
             '.rest_api_adapter.SalesforceRestAdapter')
    connection_to_patch = "%s.%s" % (klass, 'get_sf_connection')
    type_to_patch = "%s.%s" % (klass, 'get_sf_type')
    return_mock = MagicMock()
    return_mock.side_effect = _get_response
    with nested(patch(connection_to_patch, return_mock),
                patch(type_to_patch, return_mock)):
        yield
