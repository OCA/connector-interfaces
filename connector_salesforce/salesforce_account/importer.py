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
from openerp.addons.connector.unit.mapper import ImportMapper
from ..backend import salesforce_backend
from ..unit.importer_synchronizer import (
    SalesforceBatchSynchronizer,
    SalesforceDelayedBatchSynchronizer,
    SalesforceDirectBatchSynchronizer,
    SalesforceImportSynchronizer,
)
from ..unit.rest_api_adapter import SalesforceRestAdapter
@salesforce_backend
class SalesforceAccountImporter(SalesforceImportSynchronizer):
    _model_name = 'connector.salesforce.account'

@salesforce_backend
class SalesforceDirectBatchAccountImporter(SalesforceDirectBatchSynchronizer):
    _model_name = 'connector.salesforce.account'

@salesforce_backend
class SalesforceDelayedBatchAccountImporter(SalesforceDelayedBatchSynchronizer):
    _model_name = 'connector.salesforce.account'

@salesforce_backend
class SalesforceAccountAdapter(SalesforceRestAdapter):
    _model_name = 'connector.salesforce.account'
    _sf_type = 'Account'

@salesforce_backend
class SalesforceAccountMapper(ImportMapper):
    _model_name = 'connector.salesforce.account'
