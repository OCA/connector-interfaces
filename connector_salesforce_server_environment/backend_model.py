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
from openerp.addons.server_environment import serv_config
from openerp.osv import orm, fields


class odbc_backend(orm.Model):
    """Use server env. to manage auth parameters"""

    def _get_auth_columns(self):
        return [
            'authentication_method'
            'callback_url',
            'consumer_code',
            'consumer_key',
            'consumer_refresh_token',
            'consumer_secret',
            'organization_uuid',
            'password',
            'sandbox',
            'security_token',
            'username'
        ]

    def _get_env_auth_data(self, cr, uid, ids, context=None):
        res = {}
        for backend in self.browse(cr, uid, ids, context=context):
            section_data = {}
            section_name = "connector_sales_force_auth_%s" % backend.name
            if not serv_config.has_section(section_name):
                raise ValueError(
                    'Section %s does not exists' % section_name
                )
            for col in self._get_auth_columns():
                section_data[col] = serv_config.get(section_name, col)
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

        'username': fields.function(
            _get_env_auth_data,
            string='User Name',
            multi='username',
            type='char'
        ),


        'password': fields.function(
            _get_env_auth_data,
            string='Password',
            multi='password',
            type='char'
        ),

        'consumer_key': fields.function(
            _get_env_auth_data,
            string='OAuth2 Consumer Key',
            multi='conusmer_key',
            type='char'
        ),

        'consumer_secret': fields.function(
            _get_env_auth_data,
            string='OAuth2 secret',
            multi='consumer_secret',
            type='char'
        ),

        'consumer_code': fields.function(
            _get_env_auth_data,
            string='OAuth2 client authorization code',
            multi='consumer_code',
            type='char'
        ),
        'consumer_refresh_token': fields.function(
            _get_env_auth_data,
            string='OAuth2 Token',
            multi='consumer_refresh_token',
            type='char'
        ),
        'callback_url': fields.function(
            _get_env_auth_data,
            string='Public secure URL of Odoo (HTTPS)',
            multi='callback_url',
            type='char'
        ),
        'security_token': fields.function(
            _get_env_auth_data,
            string='Password flow Security API token',
            multi='security_token',
            type='char'
        ),

        'organization_uuid': fields.function(
            _get_env_auth_data,
            string='OrganizationId',
            multi='organization_uuid',
            type='char'
        ),

        'sandbox': fields.boolean(
            _get_env_auth_data,
            string='Connect on sandbox instance',
            multi='sandbox',
            type='boolean',
        ),

    }
