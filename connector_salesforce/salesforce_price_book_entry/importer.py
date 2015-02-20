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
from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.mapper import mapping, only_create
from ..backend import salesforce_backend
from ..unit.binder import SalesforceBinder
from ..unit.importer_synchronizer import (SalesforceDelayedBatchSynchronizer,
                                          SalesforceDirectBatchSynchronizer,
                                          SalesforceImportSynchronizer,
                                          import_record)
from ..unit.rest_api_adapter import SalesforceRestAdapter
from ..unit.mapper import PriceMapper
_logger = logging.getLogger(__name__)


@salesforce_backend
class SalesforcePriceBookEntryImporter(SalesforceImportSynchronizer):
    _model_name = 'connector.salesforce.pricebook.entry'

    def _to_deactivate(self):
        """Hook to check if record must be deactivated"""
        assert self.salesforce_record
        if not self.salesforce_record.get('IsActive'):
            entry_id = self.binder.to_openerp(self.salesforce_id)
            if entry_id:
                return True
        return False

    def _deactivate(self):
        """Implementation of deactivate action
        In this case we unlink the existing pricelist item
        """
        assert self.salesforce_id
        entry_id = self.binder.to_openerp(self.salesforce_id)
        self.session.unlink(self.model._name, [entry_id])

    def _before_import(self):
        """Hook called before Salesforce entry import
        To ensure coherence with porduct and import
        it if required"""
        assert self.salesforce_record
        product_binder = self.get_connector_unit_for_model(
            SalesforceBinder,
            model='connector.salesforce.product'
        )
        product_id = product_binder.to_openerp(
            self.salesforce_record['Product2Id']
        )
        if not product_id:
            if self.backend_record.sf_product_master == 'sf':
                import_record(
                    self.session,
                    'connector.salesforce.product',
                    self.backend_record.id,
                    self.salesforce_record['Product2Id']
                )


@salesforce_backend
class SalesforceDirectBatchPriceBookEntryImporter(
        SalesforceDirectBatchSynchronizer):
    _model_name = 'connector.salesforce.pricebook.entry'


@salesforce_backend
class SalesforceDelayedBatchPriceBookEntryImporter(
        SalesforceDelayedBatchSynchronizer):
    _model_name = 'connector.salesforce.pricebook.entry'


@salesforce_backend
class SalesforcePriceBookEntryAdapter(SalesforceRestAdapter):
    _model_name = 'connector.salesforce.pricebook.entry'
    _sf_type = 'PricebookEntry'


@salesforce_backend
class SalesforcePriceBookEntryMapper(PriceMapper):
    _model_name = 'connector.salesforce.pricebook.entry'

    direct = [
        ('UnitPrice', 'price_surcharge')
    ]

    @only_create
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def price_version_id(self, record):
        """Retrieve the price version using
        backend configuration"""
        currency_id = self.get_currency_id(record)
        mapping = {rec.currency_id.id: rec.pricelist_version_id.id
                   for rec in self.backend_record.sf_entry_mapping_ids}
        price_list_version_id = mapping.get(currency_id)
        if not price_list_version_id:
            raise MappingError(
                'No priceliste version configuration done for '
                'currency %s and backend %s' % (
                    record.get('CurrencyIsoCode'),
                    self.backend_record.name
                )
            )
        return {'price_version_id': price_list_version_id}

    @mapping
    def base(self, record):
        """Base field of pricelist item:
        the value `1` corresponds to Public Price
        """
        return {'base': 1}

    @mapping
    def product_id(self, record):
        sf_product_uuid = record.get('Product2Id')
        if not sf_product_uuid:
            raise MappingError(
                'No product available '
                'for salesforce record %s ' % record
            )
        product_binder = self.get_connector_unit_for_model(
            SalesforceBinder,
            model='connector.salesforce.product',
        )
        product_id = product_binder.to_openerp(
            sf_product_uuid,
            unwrap=True
        )
        if not product_id:
            raise MappingError(
                'Product is not available in ERP for record %s' % record
            )
        return {'product_id': product_id}
