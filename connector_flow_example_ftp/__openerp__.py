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
    'name': 'Example (Partner Export via FTP) for connector_flow',
    'version': '0.1',
    'description': """This module provides a demo task flow for the
*connector_flow* module. It implements a very simple export and
upload of all res.partner to an FTP server in a two-column CSV file
(name,zip code).""",
    'category': 'Connector',
    'license': 'AGPL-3',
    'author': 'initOS GmbH & Co. KG',
    'website': 'http://www.initos.com',
    'depends': [
        'connector_flow',
    ],
    'data': [
    ],
    'demo': [
        'demo/task_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'images': [
    ],
    'css': [
    ],
    'js': [
    ],
    'qweb': [
    ],
}
