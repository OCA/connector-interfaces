# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
from __future__ import absolute_import
import simplejson
from ..lib.oauth2_utils import SalesForceOauth2MAnager
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.addons.connector import session as csession, connector
from ..unit.importer_synchronizer import batch_import, delayed_batch_import
from ..unit.exporter_synchronizer import batch_export, delayed_batch_export


class SalesforceBackend(orm.Model):
    """Salesforce backend

    Please refer to connector backend documentation

    There are 2 supported ways to access a Salesforce instance
    Oauth2 flow
    -----------
    In order to use it you have to add a remote application in Salesforce
    and enable Oauth login.

    The The created remote access app must have following parameters:

    Permitted Users -->	All users may self-authorize
    Callback URL --> public_odoo_url/salesforce/oauth


    after that manage your app and:

    Once done you have to manage your app ensure the
    `Refresh token is valid until revoked` parameter is set.

    User Password flow
    ------------------
    This flow allows a user to connect to api using SOAP access
    in order to get a token. This approach is simpler but less secure
    The first is to pass the domain of your Salesforce instance
    and an access token straight to.

    If you have the full URL e.g (https://na1.salesforce.com) of your instance.

    There are also two means of authentication:
    - Using username, password and security token
    - Using IP filtering, username, password and organizationId
    """

    _name = "connector.salesforce.backend"
    _inherit = "connector.backend"
    _description = """Salesforce Backend"""
    _backend_type = "salesforce"

    def _select_versions(self, cr, uid, context=None):
        """ Available versions

        Can be inherited to add custom versions.

        :return: list of tuple of available versions
        :rtype: list
        """
        return self._select_versions_hook(cr, uid, context=context)

    def _select_versions_hook(self, cr, uid, context=None):
        """ Available versions

        Can be inherited to add custom versions.

        :return: list of tuple of available versions
        :rtype: list
        """
        return [('15', "Winter'15")]

    _columns = {
        'authentication_method': fields.selection(
            [
                ('pwd_token', 'Based on User, Password, Token'),
                ('oauth2', 'OAuth 2'),
                ('ip_filtering', 'Based on IP Filter and OrganizationId')
            ],
            string='Authentication Method',
        ),

        'name': fields.char(
            'Name',
            required=True
        ),

        'version': fields.selection(
            _select_versions,
            string='Version',
            required=True
        ),

        'url': fields.char(
            'URL',
            required=True,
        ),

        'username': fields.char(
            'User Name',
        ),

        'password': fields.char(
            'Password',
        ),

        'consumer_key': fields.char(
            'OAuth2 Consumer Key',
        ),

        'consumer_secret': fields.char(
            'OAuth2 secret',
        ),

        'consumer_code': fields.char(
            'OAuth2 client authorization code'
        ),
        'consumer_refresh_token': fields.char(
            'OAuth2 Refresh Token'
        ),
        'consumer_token': fields.char(
            'OAuth2 Token'
        ),
        'callback_url': fields.char(
            'Public secure URL of Odoo (HTTPS)',
        ),
        'security_token': fields.char(
            'Password flow Security API token',
        ),

        'organization_uuid': fields.char('OrganizationId'),

        'sandbox': fields.boolean(
            'Connect on sandbox instance',
        ),
    }

    _defaults = {'authentication_method': 'oauth2'}

    def _enforce_param(self, cr, uid, backend_record, param_name,
                       context=None):
        """Ensure configuration parameter is set on backend record

        :param backend_record: record of `connector.salesforce.backend`
        :type backend_record: :py:class:`openerp.osv.orm.Model`

        :return: True is parameter is set or raise an exception
        :rtype: bool
        """
        if not backend_record[param_name]:
            f_model = self.pool['ir.model.fields']
            field_id = f_model.search(
                cr,
                uid,
                [('model', '=', self._name),
                 ('name', '=', param_name)],
                context=context
            )
            if len(field_id) == 1:
                field = f_model.browse(
                    cr,
                    uid,
                    field_id[0],
                    context=context
                )
                field_name = field.field_description
            else:
                field_name = param_name
            raise orm.except_orm(
                _('Configuration error'),
                _('Configuration %s is mandatory with '
                  'current authentication method') % field_name
            )
        return True

    def _enforce_url(self):
        """Predicate hook to see if URL must be enforced
        when validating configuration"""
        return True

    def _validate_configuration(self, cr, uid, ids, context=None):
        """Ensure configuration on backend record is correct

        We also test required parameters in order to
        support eventual server env based configuration
        """
        for config in self.browse(cr, uid, ids, context=context):
            if self._enforce_url():
                self._enforce_param(cr, uid, config, 'url',
                                    context=context)
            if config.authentication_method == 'ip_filtering':
                self._enforce_param(cr, uid, config, 'organization_uuid',
                                    context=context)
                self._enforce_param(cr, uid, config, 'username',
                                    context=context)
                self._enforce_param(cr, uid, config, 'password',
                                    context=context)
            if config.authentication_method == 'pwd_token':
                self._enforce_param(cr, uid, config, 'security_token',
                                    context=context)
                self._enforce_param(cr, uid, config, 'username',
                                    context=context)
                self._enforce_param(cr, uid, config, 'password',
                                    context=context)
            if config.authentication_method == 'oauth2':
                self._enforce_param(cr, uid, config, 'consumer_key',
                                    context=context)
                self._enforce_param(cr, uid, config, 'consumer_secret',
                                    context=context)
                self._enforce_param(cr, uid, config, 'callback_url',
                                    context=context)
        return True

    _constraints = [
        (_validate_configuration, 'Configuration is invalid', [])
    ]

    def _manage_ids(self, ids):
        """Boilerplate to manage various ids type"""
        if isinstance(ids, (list, tuple)):
            assert len(ids) == 1, 'One id expected'
            backend_id = ids[0]
        else:
            backend_id = ids
        return backend_id

    def get_connector_environment(self, cr, uid, ids, model_name,
                                  context=None):
        """Returns a connector environment related to model and current backend

        :param model_name: Odoo model name taken form `_name` property
        :type model_name: str

        :return: a connector environment related to model and current backend
        :rtype: :py:class:``connector.Environment``

        """
        backend_id = self._manage_ids(ids)
        session = csession.ConnectorSession(
            cr,
            uid,
            context
        )
        backend = self.browse(cr, uid, backend_id, context=context)
        env = connector.Environment(backend, session, model_name)
        return env

    def _get_oauth2_handler(self, cr, uid, ids, context=None):
        """Initialize and return an instance of SalesForce OAuth2 Helper

        :return: An OAuth2 helper instance
        :rtype: :py:class:`..lib.oauth2_utils.SalesForceOauth2MAnager`
        """
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)

        oauth2_handler = SalesForceOauth2MAnager(
            current
        )
        return oauth2_handler

    def redirect_to_validation_url(self, cr, uid, ids, context=None):
        """Retrieve Oauth2 authorization URL"""
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        oauth2_handler = current._get_oauth2_handler()
        auth_url = oauth2_handler.authorize_url(
            response_type='code',
            state=simplejson.dumps(
                {'backend_id': current.id, 'dbname': cr.dbname}
            )
        )
        return {
            'name': 'Authorize Odoo/OpenERP',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': auth_url
        }

    def refresh_token(self, cr, uid, ids, context=None):
        """Refresh current backend Oauth2 token
        using the Salesforce refresh token
        """
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        current._get_token(refresh=True)
        return {}

    def _get_token(self, cr, uid, ids, refresh=False, context=None):
        """Obtain current backend Oauth2 token and or refresh Token"""
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        oauth2_handler = current._get_oauth2_handler()
        if refresh:
            if not current.consumer_refresh_token:
                raise ValueError(
                    'Trying to refresh token but no saved refresh token'
                )
            response = oauth2_handler.refresh_token()
        else:
            response = oauth2_handler.get_token()
        if response.get('error'):
            raise Exception(
                'Can not get Token: %s %s' % (
                    response['error'],
                    response['error_description']
                )
            )
        # refresh token must absolutly be saved else
        # all authorization process must be redone
        token_vals = {'consumer_token': response['access_token']}
        if response.get('refresh_token'):
            token_vals['consumer_refresh_token'] = response['refresh_token']
        current.write(token_vals)
        return response

    def _import(self, cr, uid, ids, model, mode, date_field,
                full=False, context=None):
        """Run an import for given backend and model

        :param model: The Odoo binding model name found in _name
        :type model: str
        :param mode: import mode must be in  `('direct', 'delay')`
                     if mode is delay import will be done using jobs
        :type mode: str

        :param date_field: name of the current backend column that store
                           the last import date for current import

        :return: import start time
        :rtype: str
        """
        assert mode in ('direct', 'delay'), "Invalid mode"
        import_start_time = fields.datetime.now()
        session = csession.ConnectorSession(
            cr,
            uid,
            context
        )
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        date = current[date_field] if full is False else False
        if mode == 'direct':
            batch_import(
                session,
                model,
                current.id,
                date=date
            )
        else:
            delayed_batch_import(
                session,
                model,
                current.id,
            )
        current.write({date_field: import_start_time})
        return import_start_time

    def _export(self, cr, uid, ids, model, mode, date_field,
                full=False, context=None):
        """Run an export for given backend and model

        :param model: The Odoo binding model name found in _name
        :type model: str
        :param mode: export mode must be in  `('direct', 'delay')`
                     if mode is delay export will be done using jobs
        :type mode: str

        :param date_field: name of the current backend column that store
                           the last export date for current export

        :return: export start time
        :rtype: str
        """
        assert mode in ['direct', 'delay'], "Invalid mode"
        session = csession.ConnectorSession(
            cr,
            uid,
            context
        )
        export_start_time = fields.datetime.now()
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        date = current[date_field] if full is False else False
        if mode == 'direct':
            batch_export(
                session,
                model,
                current.id,
                date=date,
            )
        else:
            delayed_batch_export(
                session,
                model,
                current.id,
                date=date
            )
        current.write({date_field: export_start_time})
        return export_start_time


class SalesforceBindingModel(orm.AbstractModel):

    _name = 'salesforce.binding'
    _inherit = 'external.binding'

    _columns = {
        'backend_id': fields.many2one(
            'connector.salesforce.backend',
            'salesforce Backend',
            required=True,
            ondelete='restrict'
        ),
        'salesforce_id':  fields.char('Salesforce ID'),
        'salesforce_sync_date': fields.datetime('Salesforce Synchro. Date')
    }
