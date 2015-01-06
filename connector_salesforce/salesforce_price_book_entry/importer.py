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
from ..unit.importer_synchronizer import (SalesforceDelayedBatchSynchronizer,
                                          SalesforceDirectBatchSynchronizer,
                                          SalesforceImportSynchronizer,
                                          import_record)
from ..unit.rest_api_adapter import SalesforceRestAdapter
from ..unit.mapper import AddressMapper
_logger = logging.getLogger('salesforce_connector_contact_import')


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
        assert self.salesforce_id
        entry_id = self.binder.to_openerp(self.salesforce_id)
        self.session.unlink(self.model._name, [entry_id])

    def _before_import(self):
        assert self.salesforce_record
        with self.session.change_context({'active_test': False}):
            product_id = self.session.search(
                'connector.salesforce.product',
                [('salesforce_id', '=', self.salesforce_record['Product2Id']),
                 ('backend_id', '=', self.backend_record.id)]
            )
        if not product_id:
            if self.backend_record.sf_product_master == 'erp':
                import_record(
                    self.session,
                    'connector.salesforce.product',
                    self.backend_record.id,
                    self.salesforce_record['Product2Id']
                )


@salesforce_backend
class SalesforceDirectBatchPriceBookEntryImporter(SalesforceDirectBatchSynchronizer):
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
class SalesforcePriceBookEntryMapper(AddressMapper):
    _model_name = 'connector.salesforce.pricebook.entry'

    direct = [
        ('UnitPrice', 'price_surcharge')
    ]

    @only_create
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    def get_currency_id(self, record):
        currency_iso_code = record.get('CurrencyIsoCode')
        if not currency_iso_code:
            raise MappingError(
                'No currency Given for price book entry: %s' % record
            )
        currency_id = self.session.search(
            'res.currency',
            [('name', '=ilike', currency_iso_code)]
        )
        if not currency_id:
            raise MappingError(
                'No %s currency available. '
                'Please create one manually' % currency_iso_code
            )
        if len(currency_id) > 1:
            raise ValueError(
                'Many Currencies found for %s. '
                'Please ensure your multicompany rules are corrects '
                'or check that the job is not runned by '
                'the admin user' % currency_iso_code
            )
        return currency_id[0]

    @mapping
    def price_version_id(self, record):
        currency_id = self.get_currency_id(record)
        backend = self.options['backend_record']
        mapping = {rec.currency_id.id: rec.pricelist_version_id.id
                   for rec in backend.sf_entry_mapping_ids}
        price_list_version_id = mapping.get(currency_id)
        if not price_list_version_id:
            raise MappingError(
                'No priceliste version configuration done for '
                'currency %s and backend %s' % (
                    record.get('CurrencyIsoCode'),
                    backend.name
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
        backend = self.options['backend_record']
        with self.session.change_context({'active_test': False}):
            bind_product_id = self.session.search(
                'connector.salesforce.product',
                [('salesforce_id', '=', sf_product_uuid),
                 ('backend_id', '=', backend.id)]
            )
        if not bind_product_id:
            raise MappingError(
                'Product is not available in ERP for record %s' % record
            )
        bind_product = self.session.browse(
            'connector.salesforce.product',
            bind_product_id[0]
        )
        return {'product_id': bind_product.openerp_id.id}
