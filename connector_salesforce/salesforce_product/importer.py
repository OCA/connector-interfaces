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
import logging
from openerp.addons.connector.unit.mapper import ImportMapper
from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.mapper import mapping, only_create
from ..backend import salesforce_backend
from ..unit.importer_synchronizer import (SalesforceDelayedBatchSynchronizer,
                                          SalesforceDirectBatchSynchronizer,
                                          SalesforceImportSynchronizer,
                                          import_record)
from ..unit.rest_api_adapter import SalesforceRestAdapter
from ..unit.mapper import AddressMapper
_logger = logging.getLogger('salesforce_connector_product_mapping')

TYPE_MAP_REGISTER = {'Service': 'service'}

@salesforce_backend
class SalesforceProductImporter(SalesforceImportSynchronizer):
    _model_name = 'connector.salesforce.product'

@salesforce_backend
class SalesforceDirectBatchProductImporter(SalesforceDirectBatchSynchronizer):
    _model_name = 'connector.salesforce.product'


@salesforce_backend
class SalesforceDelayedBatchProductImporter(
        SalesforceDelayedBatchSynchronizer):
    _model_name = 'connector.salesforce.product'


@salesforce_backend
class SalesforceProductAdapter(SalesforceRestAdapter):
    _model_name = 'connector.salesforce.product'
    _sf_type = 'Product2'


@salesforce_backend
class SalesforceProductMapper(ImportMapper):
    _model_name = 'connector.salesforce.product'

    direct = [
        ('IsActive', 'active'),
        ('ProductCode', 'code'),
        ('ProductDescription', 'description'),
        ('Name', 'name'),
    ]

    @only_create
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    def get_default_type(self):
        stock = self.session.search(
            'ir.module.module',
            [('name', '=', 'stock'),
             ('state', '=', 'installed')],
        )
        if stock:
           return 'product'
        return 'consu'

    @mapping
    def product_type(self, record):
        product_type = record.get('Family')
        if product_type:
            map = TYPE_MAP_REGISTER
            product_type = map.get(
                product_type,
                self.get_default_type()
            )
        else:
            product_type = self.get_default_type()
        return {'type': product_type}
