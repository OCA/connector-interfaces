# -*- coding: utf-8 -*-
###############################################################################
#
#   file_document for OpenERP
#   Authors: Sebastien Beau <sebastien.beau@akretion.com>
#            Benoît Guillot <benoit.guillot@akretion.com>
#   Copyright 2013 Akretion
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'file_document',
    'version': '1.0',
    'category': 'Generic Modules/Others',
    'license': 'AGPL-3',
    'description': """
Abstraction module that allow to store informations in files used to exchange datas (import/export) with any external applications (file exchange or web services)
Example : logisticians, e-commerce platforms, automated machines
""",
    'author': 'Akretion',
    'website': 'http://www.akretion.com/',
    'depends': [
        'abstract_automatic_task',
        'mail',
    ],
    'demo': [],
    'data': [
        'file_document_view.xml',
        'file_document_data.xml',
        'security/ir.model.access.csv',
        'security/file_document_security.xml',
    ],
    'installable': True,
    'active': False,
}
