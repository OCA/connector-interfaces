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
from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.mapper import mapping, only_create
from ..backend import salesforce_backend
from ..unit.importer_synchronizer import (SalesforceDelayedBatchSynchronizer,
                                          SalesforceDirectBatchSynchronizer,
                                          SalesforceImportSynchronizer)
from ..unit.rest_api_adapter import SalesforceRestAdapter
from ..unit.mapper import AddressMapper


_logger = logging.getLogger('salesforce_connector_account_import')


@salesforce_backend
class SalesforceAccountImporter(SalesforceImportSynchronizer):
    _model_name = 'connector.salesforce.account'

    def _after_import(self, binding_id):
        # Can be used in Mapper.finalize but
        # managin nested syntax when updating would have been a mess
        record_mapper = self.mapper
        shipping_add_data = record_mapper.map_shipping_address(
            self.salesforce_record,
            binding_id,
        )
        self.session.write(self._model_name, [binding_id], shipping_add_data)


@salesforce_backend
class SalesforceDirectBatchAccountImporter(SalesforceDirectBatchSynchronizer):
    _model_name = 'connector.salesforce.account'


@salesforce_backend
class SalesforceDelayedBatchAccountImporter(
        SalesforceDelayedBatchSynchronizer):
    _model_name = 'connector.salesforce.account'


@salesforce_backend
class SalesforceAccountAdapter(SalesforceRestAdapter):
    _model_name = 'connector.salesforce.account'
    _sf_type = 'Account'


@salesforce_backend
class SalesforceAccountMapper(AddressMapper):
    _model_name = 'connector.salesforce.account'

    direct = [
        ('Name', 'name'),
        ('BillingStreet', 'street'),
        ('BillingPostalCode', 'zip'),
        ('BillingCity', 'city'),
        ('Fax', 'fax'),
        ('Phone', 'phone'),
        ('VATNumber__c', 'vat'), # To support commonly installed VAT application
    ]

    def _prepare_shipp_addresse_data(self, record, partner_record):
        """Convert shipping address information to res.partner data dict"""
        data = {
            'name': record['Name'],
            'street': record['ShippingStreet'],
            'zip': record['ShippingPostalCode'],
            'city': record['ShippingCity'],
            'state': record['ShippingState'],
            'phone': record['Phone'],
            'parent_id': partner_record.openerp_id.id,
            'type': 'delivery',
            'customer': True,

        }
        country_id = self._country_id(record, 'ShippingCountryCode')
        data['country_id'] = country_id
        state_id = self._state_id(record,
                                  'ShippingState',
                                  'ShippingCountryCode')
        data['state_id'] = state_id
        return data

    def map_shipping_address(self, record, binding_id=None):
        """Manage the Salesforce account shipping address
        If no shipping address exist in Odoo it is created.
        If a shipping address already exists we update it.
        If no shipping data are present and a shipping adress exists
        it will be unactivated

        """
        if not binding_id:
            raise MappingError(
                'No binding_id when mapping shipping address'
            )
        current_partner = self.session.browse(
            self._model_name,
            binding_id,
        )
        shipp_id = None
        shipp_fields = (field for field in record
                        if field.startswith('Shipping'))
        if any(record[field] for field in shipp_fields):
            if current_partner.sf_shipping_partner_id:
                shipp_id = current_partner.sf_shipping_partner_id.id
                self.session.write(
                    'res.partner',
                    [current_partner.sf_shipping_partner_id.id],
                    self._prepare_shipp_addresse_data(record, current_partner)
                )
            else:
                shipp_id = self.session.create(
                    'res.partner',
                    self._prepare_shipp_addresse_data(record, current_partner)
                )
        else:
            shipp_id = False
            if current_partner.sf_shipping_partner_id:
                self.session.write(
                    'res.partner',
                    [current_partner.sf_shipping_partner_id.id],
                    {'active': False}
                )
        return {'sf_shipping_partner_id': shipp_id}

    @only_create
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @only_create
    @mapping
    def is_company(self, record):
        return {'is_company': True}

    @mapping
    def country_id(self, record):
        country_id = self._country_id(record, 'BillingCountryCode')
        return {'country_id': country_id}

    @mapping
    def state_id(self, record):
        state_id = self._state_id(record, 'BillingState', 'BillingCountryCode')
        return {'state_id': state_id}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def active(self, record):
        return {'active': True}
