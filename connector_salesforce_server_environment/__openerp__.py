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
{'name': 'Connector Salesforce Server Environment',
 'version': '0.1',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Tools',
 'complexity': 'normal',
 'depends': ['server_environment', 'connector_salesforce'],
 'description': """Implements server environment behavior
for connector Salesforce authentication.

 To use it you have to add a section named as:

    salesforce_auth_ + Name of the backend

 Default svailable section options are:

 - authentication_method
 - callback_url
 - sandbox
 - url

Module can easily be extended to add any other fields.
By default they are not provided in order not have security issues
 """,
 'website': 'http://www.camptocamp.com',
 'data': [],
 'demo': [],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
