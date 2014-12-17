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
                                          SalesforceImportSynchronizer,
                                          import_record)
from ..unit.rest_api_adapter import SalesforceRestAdapter
from ..unit.mapper import AddressMapper
_logger = logging.getLogger('salesforce_connector_contact_import')


@salesforce_backend
class SalesforceContactImporter(SalesforceImportSynchronizer):
    _model_name = 'connector.salesforce.contact'

    def _before_import(self):
        assert self.salesforce_record
        account_id = self.session.search(
            'connector.salesforce.account',
            [('salesforce_id', '=', self.salesforce_record['AccountId'])]
        )
        if not account_id:
            import_record(
                self.session,
                'connector.salesforce.account',
                self.backend_record.id,
                self.salesforce_record['AccountId']
            )


@salesforce_backend
class SalesforceDirectBatchContactImporter(SalesforceDirectBatchSynchronizer):
    _model_name = 'connector.salesforce.contact'


@salesforce_backend
class SalesforceDelayedBatchContactImporter(
        SalesforceDelayedBatchSynchronizer):
    _model_name = 'connector.salesforce.contact'


@salesforce_backend
class SalesforceContactAdapter(SalesforceRestAdapter):
    _model_name = 'connector.salesforce.contact'
    _sf_type = 'Contact'


@salesforce_backend
class SalesforceContactMapper(AddressMapper):
    _model_name = 'connector.salesforce.contact'

    direct = [
        ('MailingStreet', 'street'),
        ('MailingPostalCode', 'zip'),
        ('MailingCity', 'city'),
        ('Fax', 'fax'),
        ('Phone', 'phone'),
        ('sf_assistant_phone', 'sf_assistant_phone'),
        ('OtherPhone', 'sf_other_phone'),
        ('MobilePhone', 'mobile'),
        ('Title', 'function'),
        ('Email', 'email')
    ]

    @only_create
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @only_create
    @mapping
    def is_company(self, record):
        return {'is_company': False}

    @only_create
    @mapping
    def name(self, record):
        compound_name = ' '.join((record['LastName'], record['FirstName']))
        return {'name': compound_name}

    @mapping
    def country_id(self, record):
        country_id = self._country_id(record, 'MailingCountryCode')
        return {'country_id': country_id}

    @mapping
    def state_id(self, record):
        state_id = self._state_id(record, 'MailingState', 'MailingCountryCode')
        return {'state_id': state_id}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def active(self, record):
        return {'active': True}

    @mapping
    def title_id(self, record):
        title_id = self._title_id(record, 'Salutation')
        return {'title': title_id}

    @mapping
    def parent_id(self, record):
        parent_id = self.session.search(
            'connector.salesforce.account',
            [('salesforce_id', '=', record['AccountId'])]
        )
        if not parent_id:
            raise MappingError(
                'No Account (parent partner) imported for Contact %s' % record
            )
        parent = self.session.browse(
            'connector.salesforce.account',
            parent_id[0]
        )
        return {'parent_id': parent.openerp_id.id}
