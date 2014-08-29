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
 'complexity': "normal",  # easy, normal, expert
 'depends': ['connector'],
 'description': """synchronize data from odbc compatible DB""",
 'data': ['view/backend_view.xml'],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
