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
from openerp.addons.connector.unit.mapper import ImportMapper
from openerp.addons.connector.exception import MappingError


class AddressMapper(ImportMapper):

    def _state_id(self, record, state_key, country_key):
        state = record.get(state_key)
        if not state:
            return False
        state_id = self.session.search(
            'res.country.state',
            [('name', '=', state)]
        )
        if state_id:
            return state_id[0]
        else:
            country_id = self._country_id(record, country_key)
            if country_id:
                return self.session.create(
                    'res.country.state',
                    {'name': state,
                     'country_id': country_id}
                )
        return False

    def _country_id(self, record, country_key):
        """Map Salesforce countrycode to Odoo code"""
        country_code = record.get(country_key)
        if not country_code:
            return False
        country_id = self.session.search(
            'res.country',
            [('code', '=', country_code)]
        )
        # we tolerate the fact that country is null
        if len(country_id) > 1:
            raise MappingError(
                'Many countries found to be linked with partner %s' % record
            )

        if not country_id:
            country_id = False
            raise MappingError(
                "No country %s found when mapping partner %s" % (
                    country_code,
                    record
                )
            )
        return country_id[0] if country_id else False

    def _title_id(self, record, title_key):
        title = record.get(title_key)
        if not title:
            return False
        title_id = self.session.search(
            'res.partner.title',
            [('name', '=', title)],
        )
        if len(title_id) > 1:
            raise MappingError(
                'Many countitle found to be linked with partner %s' % record
            )
        if title_id:
            return title_id[0]
        return self.session.create(
            'res.partner.title',
            {'name': title}
        )
