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
    'name': 'Connector-based task flow for import/export',
    'version': '0.1',
    'description': """This module provides a minimal framework for common
data import/export tasks based on the OpenERP Connector. Tasks like parsing
and writing a CSV file or uploading a file to an FTP server can be chained
into task flows.

At the moment every flow must a have a unique start. One task can trigger
several tasks.

The module adds a new menu item "Import/Export" under the Connector top-level
menu where tasks and task flows can be configured. Tasks can be run from
the "Run Task" wizard. If a task needs a file as input, a file can be uploaded
in the wizard.

The *connector_flow_example_{ftp,product}* modules provide pre-configured
demo flows.

This module was definitely inspired by the works of Akretion (file_repository)
and Camptocamp (connector_file).""",
    'category': 'Connector',
    'author': 'initOS GmbH & Co. KG',
    'license': 'AGPL-3',
    'website': 'http://www.initos.com',
    'depends': [
        'connector',
        'fix_bug_1316948',
    ],
    'external_dependencies': {
        'python': ['ftputil'],
    },
    'data': [
        'impexp_task_view.xml',
        'file_view.xml',
        'chunk_view.xml',
        'wizard/run_task_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
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
