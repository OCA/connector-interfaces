# -*- coding: utf-8 -*-
###############################################################################
#
#   file_repository for OpenERP
#   Authors: Emmanuel Samyn <emmanuel.samyn@akretion.com>
#            Sebastien Beau <sebastien.beau@akretion.com>
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
    'name': 'file_repository',
    'version': '1.0',
    'category': 'Generic Modules/Others',
    'license': 'AGPL-3',
    'description': """
Abstraction module that define file management parameters (location, protocol, access)
to connect towards file storage places (external or internal).
It's used by logistician_ modules to send csv file to external warehouse
""",
    'author': 'Akretion',
    'website': 'http://www.akretion.com/',
    'depends': [
        'file_autotask_rel',
    ],
    'demo': [],
    'data': [
        'file_repository_view.xml',
        'file_document_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'active': False,
}
