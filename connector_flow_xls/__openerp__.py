# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 initOS GmbH & Co. KG (<http://www.initos.com>).
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

{
    'name': 'XLS Import for connector_flow',
    'version': '8.0.1.0.0',
    'category': 'Connector',
    'author': 'initOS GmbH & Co. KG,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'http://www.initos.com',
    'depends': [
        'connector_flow',
    ],
    'external_dependencies': {
        'python': ['xlrd'],
    },
    'data': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
