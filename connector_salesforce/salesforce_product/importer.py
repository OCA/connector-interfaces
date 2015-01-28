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
from openerp.addons.connector.unit.mapper import mapping, only_create
from ..backend import salesforce_backend
from ..unit.importer_synchronizer import (SalesforceDelayedBatchSynchronizer,
                                          SalesforceDirectBatchSynchronizer,
                                          SalesforceImportSynchronizer)

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
class SalesforceProductMapper(ImportMapper):
    _model_name = 'connector.salesforce.product'

    direct = [
        ('IsActive', 'active'),
        ('ProductCode', 'code'),
        ('Description', 'description'),
        ('Name', 'name'),
    ]

    @only_create
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def sale_ok(self, record):
        return {'sale_ok': True}

    @mapping
    def product_type(self, record, **kwargs):
        backend = self.options['backend_record']
        family = record.get('Family')
        mapping = {rec.sf_family: rec.product_type
                   for rec in backend.sf_product_type_mapping_ids}
        product_type = mapping.get(family)
        if not product_type:
            return {}
        return {'type': product_type}
