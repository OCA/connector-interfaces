# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import _, exceptions

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

from ..log import logger


class ImportMapper(Component):
    _name = "importer.base.mapper"
    _inherit = ["importer.base.component", "base.import.mapper"]
    _usage = "importer.mapper"

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
        # use the same name and prefix it w/ double underscore, like:
        # {'__foo': 'baz', 'foo': '__baz'}
    }

    def required_keys(self, create=False):
        """Return required keys for this mapper.

        The importer can use this to determine if a line
        has to be skipped.

        The recordset will use this to show required fields to users.
        """
        req = dict(self.required)
        req.update(self.work.options.mapper.get("required_keys", {}))
        return req

    translatable = []

    def translatable_keys(self, create=False):
        """Return translatable keys for this mapper.

        The importer can use this to translate specific fields
        if the are found in the csv in the form `field_name:lang_code`.

        The recordset will use this to show translatable fields to users.
        """
        translatable = list(self.translatable)
        translatable += self.work.options.mapper.get("translatable_keys", [])
        translatable = self._validate_translate_keys(set(translatable))
        return tuple(translatable)

    def _validate_translate_keys(self, translatable):
        valid = []
        fields_spec = self.model.fields_get(translatable)
        for fname in translatable:
            if not fields_spec.get(fname):
                logger.error("%s - translate key not found: `%s`.", self._name, fname)
                continue
            if not fields_spec[fname]["translate"]:
                logger.error("%s - `%s` key is not translatable.", self._name, fname)
                continue
            valid.append(fname)
        return valid

    defaults = [
        # odoo field, value
        # ('sale_ok', True),
        # defaults can be also retrieved via xmlid to other records.
        # The format is: `_xmlid::$record_xmlid::$record_field_value`
        # whereas `$record_xmlid` is the xmlid to retrieve
        # and ``$record_field_value` is the field to be used as value.
        # Example:
        # ('company_id', '_xmlid::base.main_company:id'),
    ]

    @mapping
    def default_values(self, record=None):
        """Return default values for this mapper.

        The recordset will use this to show default values to users.
        """
        values = {}
        for k, v in self.defaults:
            if isinstance(v, str) and v.startswith("_xmlid::"):
                real_val = v.replace("_xmlid::", "").strip()
                if not real_val or ":" not in real_val:
                    raise exceptions.UserError(
                        _("Malformated xml id ref: `%s`") % real_val
                    )
                xmlid, field_value = real_val.split(":")
                v = self.env.ref(xmlid)[field_value]
            values[k] = v
        values.update(self.work.options.mapper.get("default_keys", {}))
        return values
