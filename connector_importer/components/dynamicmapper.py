# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

from ..utils.mapper_utils import backend_to_rel, convert, xmlid_to_rel


class DynamicMapper(Component):
    """A mapper that dynamically converts input data to odoo fields values."""

    _name = "importer.mapper.dynamic"
    _inherit = "importer.base.mapper"
    _usage = "importer.dynamicmapper"

    @mapping
    def dynamic_fields(self, record):
        """Resolve values for non mapped keys.

        Source keys = destination keys.
        """
        if not isinstance(getattr(self, "_apply_on", None), str):
            # cannot work w/ non models or multiple models
            return {}
        vals = {}
        available_fields = self.env[self._apply_on].fields_get()
        for fname in self._non_mapped_keys(record):
            if available_fields.get(fname):
                fspec = available_fields.get(fname)
                ftype = fspec["type"]
                if self._is_xmlid_key(fname, ftype):
                    fname = fname.replace("xid:", "")
                    ftype = "_xmlid"
                converter = self._get_converter(fname, ftype)
                if converter:
                    vals[fname] = converter(self, record, fname)
        return vals

    def _is_xmlid_key(self, fname, ftype):
        return fname.startswith("xid:") and ftype in (
            "many2one",
            "one2many",
            "many2many",
        )

    def _dynamic_keys_mapping(self, fname):
        return {
            "char": lambda self, rec, fname: rec[fname],
            "integer": convert(fname, "safe_int"),
            "float": convert(fname, "safe_float"),
            "boolean": convert(fname, "bool"),
            "date": convert(fname, "date"),
            "datetime": convert(fname, "utc_date"),
            "many2one": backend_to_rel(fname),
            "many2many": backend_to_rel(fname),
            "one2many": backend_to_rel(fname),
            "_xmlid": xmlid_to_rel(fname),
        }

    def _get_converter(self, fname, ftype):
        return self._dynamic_keys_mapping(fname).get(ftype)

    _non_mapped_keys_cache = None

    def _non_mapped_keys(self, record):
        if self._non_mapped_keys_cache is None:
            all_keys = {k for k in record.keys() if not k.startswith("_")}
            mapped_keys = set()
            # NOTE: keys coming from `@mapping` methods can't be tracked.
            # Worse case: they get computed twice.
            # TODO: make sure `dynamic_fields` runs at the end
            # or move it to `finalize`
            for pair in self.direct:
                if isinstance(pair[0], str):
                    mapped_keys.add(pair[0])
                elif hasattr(pair[0], "_from_key"):
                    mapped_keys.add(pair[0]._from_key)
            self._non_mapped_keys_cache = tuple(all_keys - mapped_keys)
        return self._non_mapped_keys_cache
