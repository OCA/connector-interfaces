# -*- coding: utf-8 -*-
# Author: Simone Orsi
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp.addons.connector.unit.mapper import ImportMapper, mapping


class BaseImportMapper(ImportMapper):

    required = {
        # source key: dest key
        # You can declare here the keys the importer must have
        # to import a record.
        # `source key` means a key in the source record
        # either a line in a csv file or a lien from an sql table.
        # `dest key` is the destination the for the source one.

        # Eg: in your mapper you could have a mapping like
        #     direct = [
        #         ('title', 'name'),
        #         (concat(('title', 'foo', ), separator=' - '), 'baz'),
        #     ]
        # You want the record to be skipped if:
        # 1. title or name are not valued in the source
        # 2. title is valued but the conversion gives an empty value for name
        # 3. title or foo are not valued in the source
        # 4. title and foo are valued but the conversion
        #    gives an empty value for baz

        # You can achieve this like:
        # required = {
        #     'title': ('name', 'baz'),
        #     'foo': 'baz',
        # }

        # If you want to check only the source or the destination key
        # use the same and prefix in w/ double underscore, like:

        # {'__foo': 'baz', 'foo': '__baz'}
    }

    def required_keys(self, create=False):
        """Return required keys for this mapper.

        The importer can use this to determine if a line
        has to be skipped.
        """
        return self.required

    translatable = []

    def translatable_keys(self, create=False):
        """Return translatable keys for this mapper.

        The importer can use this to translate specific fields
        if the are found in the csv in the form `field_name:lang_code`.
        """
        return self.translatable

    defaults = [
        # odoo field, value
        # ('sale_ok', True),
    ]

    @mapping
    def default_values(self, record=None):
        return dict(self.defaults)
