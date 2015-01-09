# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
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
from collections import namedtuple
from openerp.addons.server_environment import serv_config
from openerp.osv import orm, fields

AuthField = namedtuple('AuthField', ['name', 'is_mandatory'])

class odbc_backend(orm.Model):
    """Use server env. to manage auth parameters"""

    def _get_auth_columns(self):
        return [
            AuthField('authentication_method', True),
            AuthField('callback_url', False),
            AuthField('url', True),
            AuthField('sandbox', True),
        ]

    def _get_env_auth_data(self, cr, uid, ids, context=None):
        res = {}
        for backend in self.browse(cr, uid, ids, context=context):
            section_data = {}
            section_name = "salesforce_auth_%s" % backend.name
            if not serv_config.has_section(section_name):
                raise ValueError(
                    'Section %s does not exists' % section_name
                )
            for col in self._get_auth_columns():
                if serv_config.has_option(section_name, col.name):
                    section_data[col] = serv_config.get(section_name, col.name)
                else:
                    section_data[col] = False
                if col.is_mandatory and not section_data[col]:
                    raise ValueError(
                        'Key %s not set in config file for section' % (
                            col.name,
                            section_name
                        )
                    )
            res[backend.id] = section_data
        return res

    _inherit = "connector.salesforce.backend"

    _columns = {

        'authentication_method': fields.function(
            _get_env_auth_data,
            string='Authentication Method',
            multi='authentication_method',
            type='char'
        ),

        'callback_url': fields.function(
            _get_env_auth_data,
            string='Public secure URL of Odoo (HTTPS)',
            multi='callback_url',
            type='char'
        ),

        'url': fields.function(
            _get_env_auth_data,
            string='URL',
            multi='url',
            type='char'
        ),

        'sandbox': fields.function(
            _get_env_auth_data,
            string='Connect on sandbox instance',
            multi='sandbox',
            type='boolean',
        ),
    }
