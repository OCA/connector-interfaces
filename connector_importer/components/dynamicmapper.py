# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

from ..log import logger
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
        # TODO: add tests!
        model = self.work.model_name
        vals = {}
        available_fields = self.env[model].fields_get()
        prefix = self._source_key_prefix
        clean_record = self._clean_record(record)
        required_keys = self._required_keys()
        missing_required_keys = []
        for source_fname in self._non_mapped_keys(clean_record):
            if source_fname in ("id", "xid::id"):
                # Never convert IDs
                continue
            fname = source_fname
            if "::" in fname:
                # Eg: transformers like `xid::``
                fname = fname.split("::")[-1]
                clean_record[fname] = clean_record.pop(source_fname)
            if prefix and fname.startswith(prefix):
                # Eg: prefix all supplier fields w/ `supplier.`
                fname = fname[len(prefix) :]
                clean_record[fname] = clean_record.pop(prefix + fname)
            final_fname = self._get_field_name(fname, clean_record)
            if final_fname != fname:
                clean_record[final_fname] = clean_record.pop(fname)
                fname = final_fname

            if available_fields.get(fname):
                fspec = available_fields.get(fname)
                ftype = fspec["type"]
                if self._is_xmlid_key(source_fname, ftype):
                    ftype = "_xmlid"
                converter = self._get_converter(fname, ftype)
                if converter:
                    value = converter(self, clean_record, fname)
                    if not value:
                        if source_fname in self._source_key_empty_skip:
                            continue
                        if fname in required_keys:
                            missing_required_keys.append(fname)
                    vals[fname] = value
                else:
                    logger.debug(
                        "Dynamic mapper cannot find converte for field `%s`", fname
                    )
        if missing_required_keys:
            vals.update(self._get_defaults(missing_required_keys))
            for k in missing_required_keys:
                if k in vals and not vals[k]:
                    # Discard empty values for required keys.
                    # Avoids overriding values that might be already set
                    # and that cannot be emptied.
                    vals.pop(k)
        return vals

    def _clean_record(self, record):
        valid_keys = self._get_valid_keys(record)
        return {k: v for k, v in record.items() if k in valid_keys}

    def _get_valid_keys(self, record):
        valid_keys = [k for k in record.keys() if not k.startswith("_")]
        prefix = self._source_key_prefix
        if prefix:
            valid_keys = [k for k in valid_keys if prefix in k]
        whitelist = self._source_key_whitelist
        if whitelist:
            valid_keys = [k for k in valid_keys if k in whitelist]
        blacklist = self._source_key_blacklist
        if blacklist:
            valid_keys = [k for k in valid_keys if k not in blacklist]
        return tuple(valid_keys)

    def _required_keys(self):
        return [k for k, v in self.model.fields_get().items() if v["required"]]

    @property
    def _source_key_whitelist(self):
        return self.work.options.mapper.get("source_key_whitelist", [])

    @property
    def _source_key_blacklist(self):
        return self.work.options.mapper.get("source_key_blacklist", [])

    @property
    def _source_key_empty_skip(self):
        """List of source keys to skip when empty.

        Use cases:

            * field w/ unique constraint but not populated (eg: product barcode)
            * field not to override when empty
        """
        return self.work.options.mapper.get("source_key_empty_skip", [])

    @property
    def _source_key_prefix(self):
        return self.work.options.mapper.get("source_key_prefix", "")

    @property
    def _source_key_rename(self):
        return self.work.options.mapper.get("source_key_rename", {})

    def _get_field_name(self, fname, clean_record):
        """Return final field name.

        Field names can be manipulated via mapper option `source_key_rename`
        which must be a dictionary w/ source name -> destination name.
        """
        return self._source_key_rename.get(fname, fname)

    def _is_xmlid_key(self, fname, ftype):
        return fname.startswith("xid::") and ftype in (
            "many2one",
            "one2many",
            "many2many",
        )

    def _dynamic_keys_mapping(self, fname, **options):
        return {
            "char": lambda self, rec, fname: rec[fname],
            "text": lambda self, rec, fname: rec[fname],
            "selection": lambda self, rec, fname: rec[fname],
            "integer": convert(fname, "safe_int", **options),
            "float": convert(fname, "safe_float", **options),
            "boolean": convert(fname, "bool", **options),
            "date": convert(fname, "date", **options),
            "datetime": convert(fname, "utc_date", **options),
            "many2one": backend_to_rel(fname, **options),
            "many2many": backend_to_rel(fname, **options),
            "one2many": backend_to_rel(fname, **options),
            "_xmlid": xmlid_to_rel(fname, **options),
        }

    def _get_converter(self, fname, ftype):
        options = self.work.options.mapper.get("converter", {}).get(fname, {})
        return self._dynamic_keys_mapping(fname, **options).get(ftype)

    _non_mapped_keys_cache = None

    def _non_mapped_keys(self, record):
        if self._non_mapped_keys_cache is None:
            all_keys = set(record.keys())
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

    def _get_defaults(self, fnames):
        return self.model.default_get(fnames)
