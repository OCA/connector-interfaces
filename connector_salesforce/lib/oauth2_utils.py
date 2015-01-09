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
import requests
from urllib import quote, urlencode
from urlparse import parse_qs, urljoin
import simplejson as json


class SalesForceOauth2MAnager(object):

    def __init__(self, backend_record):
        """
        """
        self.backend = backend_record
        self.base_login_url = 'https://login.salesforce.com/'
        self.authorization_url = "services/oauth2/authorize"
        self.token_url = "services/oauth2/token"
        self.redirect_uri = urljoin(self.backend.callback_url,
                                    "salesforce/oauth")
        if self.backend.sandbox:
            self.base_login_url = "https://test.salesforce.com/"

    def authorize_url(self, scope='', **kwargs):
        """
        Returns the callback url to redirect the user after authorization
        """

        oauth_params = {
            'redirect_uri': self.redirect_uri,
            'client_id': self.backend.consumer_key,
            'scope': scope
        }
        oauth_params.update(kwargs)
        return "%s%s?%s" % (
            self.base_login_url,
            quote(self.authorization_url),
            urlencode(oauth_params)
        )

    def get_token(self, **kwargs):
        """
        Requests an access token
        """
        url = "%s%s" % (self.base_login_url, quote(self.token_url))
        data = {'code': self.backend.consumer_code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri,
                'client_id': self.backend.consumer_key,
                'client_secret': self.backend.consumer_secret}
        data.update(kwargs)
        response = requests.post(url, data=data)

        if isinstance(response.content, basestring):
            try:
                content = json.loads(response.content)
            except ValueError:
                content = parse_qs(response.content)
        else:
            content = response.content
        return content

    def refresh_token(self, **kwargs):
        """
        Requests an access token
        """
        url = "%s%s" % (self.base_login_url, quote(self.token_url))
        data = {'refresh_token': self.backend.consumer_refresh_token,
                'client_id': self.backend.consumer_key,
                'client_secret': self.backend.consumer_secret,
                'grant_type': 'refresh_token'}
        data.update(kwargs)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(url, data=data, headers=headers)
        if isinstance(response.content, basestring):
            try:
                content = json.loads(response.content)
            except ValueError:
                content = parse_qs(response.content)
        else:
            content = response.content
        return content
