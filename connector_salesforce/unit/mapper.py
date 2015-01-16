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
                'Many titles found to be linked with partner %s' % record
            )
        if title_id:
            return title_id[0]
        return self.session.create(
            'res.partner.title',
            {'name': title}
        )


class PriceMapper(ImportMapper):

    def get_currency_id(self, record):
        currency_iso_code = record.get('CurrencyIsoCode')
        if not currency_iso_code:
            raise MappingError(
                'No currency Given for: %s' % record
            )
        currency_id = self.session.search(
            'res.currency',
            [('name', '=ilike', currency_iso_code)]
        )
        if not currency_id:
            raise MappingError(
                'No %s currency available. '
                'Please create one manually' % currency_iso_code
            )
        if len(currency_id) > 1:
            raise ValueError(
                'Many Currencies found for %s. '
                'Please ensure your multicompany rules are corrects '
                'or check that the job is not runned by '
                'the admin user' % currency_iso_code
            )
        return currency_id[0]
