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
import simplejson
from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager
import openerp.addons.web.http as oeweb


class SalesforceOAuthController(oeweb.Controller):
    """Controller that is used to authenticate
    Salesforce using oauth2. This is used
    as the callback URL and it will register tocken
    into `connector.salesforce.backend`
    """
    _cp_path = '/salesforce'

    @oeweb.httprequest
    def oauth(self, req, **kwargs):
        """Write Salesforce authorization
        Token in given backend.

        Backend token and backend are GET parameters

        :param req: WSGI request
        :return: success message or raise an error
        :rtype: str
        """
        code = req.params.get('code')
        state = req.params.get('state')
        if not all([code, state]):
            raise ValueError(
                'Authorization process went wrong '
                'with following error %s' % req.params
            )
        try:
            state_data = simplejson.loads(state)
            backend_id = state_data['backend_id']
            dbname = state_data['dbname']
        except Exception:
            raise ValueError(
                'The authorization process did not return valid values'
            )
        registry = RegistryManager.get(dbname)
        with registry.cursor() as cr:
            backend_model = registry.get('connector.salesforce.backend')
            backend = backend_model.browse(cr, SUPERUSER_ID, backend_id)
            if not backend:
                raise ValueError('No backend with id %s' % backend_id)
            backend.write({'consumer_code': code})
            # In Salesforce you have a limited time to ask first token
            # after getting conusmer code, else code becomme invalid
            backend._get_token()
        return ("Backend successfuly authorized you should have a new "
                "authorization code in your backend")
