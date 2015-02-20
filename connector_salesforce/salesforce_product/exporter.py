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
import logging
from openerp.addons.connector.unit.mapper import ExportMapper
from openerp.addons.connector.unit.mapper import mapping
from ..backend import salesforce_backend
from ..unit.exporter_synchronizer import (SalesforceDelayedBatchSynchronizer,
                                          SalesforceDirectBatchSynchronizer,
                                          SalesforceExportSynchronizer)

_logger = logging.getLogger('salesforce_connector_product_export_mapping')

TYPE_MAP_REGISTER = {'Service': 'service'}


@salesforce_backend
class SalesforceProductExporter(SalesforceExportSynchronizer):
    _model_name = 'connector.salesforce.product'

    def _to_deactivate(self):
        """Implement predicate that decide if product
        must be deactivated in Odoo
        """
        assert self.binding_record
        if not self.binding_record.active or not self.binding_record.sale_ok:
            return True
        return False


@salesforce_backend
class SalesforceDirectBatchProductExporter(SalesforceDirectBatchSynchronizer):
    _model_name = 'connector.salesforce.product'


@salesforce_backend
class SalesforceDelayedBatchProductExporter(
        SalesforceDelayedBatchSynchronizer):
    _model_name = 'connector.salesforce.product'


@salesforce_backend
class SalesforceProductMapper(ExportMapper):
    _model_name = 'connector.salesforce.product'

    direct = [
        ('active', 'IsActive',),
        ('code', 'ProductCode'),
        ('description', 'Description'),
        ('name', 'Name'),
    ]

    @mapping
    def product_type(self, record):
        backend = record.backend_id
        mapping = {rec.product_type: rec.sf_family
                   for rec in backend.sf_product_type_mapping_ids}
        family = mapping.get(record.type)
        if not family:
            return {}
        return {'Family': family}
