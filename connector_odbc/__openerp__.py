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
{'name': 'ODBC data synchronizer',
 'version': '0.1',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Connector',
 'complexity': "normal",
 'depends': ['connector'],
 'description': """
Import data from other databases using connector Framework.
Synchronize data from odbc compatible Database source.
You will find in test a sample of implementation.

Under the sample folder you will find sample
demonstrating the most common use cases.

When importing hierarchical data do not forget to
manage `defer_parent_store_computation` in context.

There is an open issue with the management of the
priority in connector. When using delayed
import, if you have a task with
a high priority that generates a lot job
it may prevent task with lower priority to be imported
""",
 'data': ['data.xml',
          'view/backend_view.xml'],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
