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
from openerp.addons.connector.exception import (ConnectorException,
                                                RetryableJobError)
class SalesforceRESTAPIError(ConnectorException):
    """Rest API error"""

class SalesforceSecurityError(SalesforceRESTAPIError):
    """Authentication error with Salesforce"""

class SalesforceResponseError(SalesforceRESTAPIError):
    """Map simple_salesforce error to connector error"""
    def __init__(self, sf_error):
        self.sf_error = sf_error

    def __str__(self):
        return repr(self.sf_error)


class SalesforceQuotaError(RetryableJobError):
    """To be used when API call quota is consumed to postpone the job"""
