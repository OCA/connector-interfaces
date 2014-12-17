# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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
{'name': 'Salesforce connector',
 'version': '0.1',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Connector',
 'complexity': "normal",
 'depends': ['connector', 'sale', 'product'],
 'summary': """Provides core import export interfaces with Salesforce.""",
 'description': """
Provides core import export interfaces with Salesforce.
Manage number of rest call limitation.

By default following action are supported:

- Import of Account and contact into OpenERP/Odoo Salesforce is the master
- Import of Product and PriceBook entries into OpenERP/Odoo
  Salesforce is the master
- Import of chosen Opportunity into OpenERP/Odoo Salesforce is the master

Parent relation of Account is not supported at that time

Export to Salesforce are supported and implemented but
there is no default export provided at current time.

""",
 'data': [
     'view/backend_model_view.xml',
     'salesforce_account/view/backend_view.xml',
     'salesforce_contact/view/backend_view.xml',
     'salesforce_contact/view/res_partner_view.xml',
 ],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
