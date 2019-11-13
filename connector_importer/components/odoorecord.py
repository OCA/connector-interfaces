# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class OdooRecordHandler(Component):
    """Interact w/ odoo importable records."""

    _name = "importer.odoorecord.handler"
    _inherit = "importer.base.component"
    _usage = "odoorecord.handler"

    unique_key = ""
    unique_key_is_xmlid = False
    importer = None
    # By default odoo ignores create_uid/write_uid in vals.
    # If you enable this flags and `create_uid` and/or `write_uid`
    # are found in values they gonna be used for sudo.
    # Same for `create_date`.
    override_create_uid = False
    override_create_date = False
    override_write_uid = False

    def _init_handler(self, importer=None, unique_key=None, unique_key_is_xmlid=False):
        self.importer = importer
        self.unique_key = unique_key
        self.unique_key_is_xmlid = unique_key_is_xmlid

    def odoo_find_domain(self, values, orig_values):
        """Domain to find the record in odoo."""
        return [(self.unique_key, "=", values[self.unique_key])]

    def odoo_find(self, values, orig_values):
        """Find any existing item in odoo."""
        if not self.unique_key:
            return self.model
        if self.unique_key_is_xmlid:
            item = self.env.ref(values[self.unique_key], raise_if_not_found=False)
            return item
        item = self.model.search(
            self.odoo_find_domain(values, orig_values),
            order="create_date desc",
            limit=1,
        )
        return item

    def odoo_exists(self, values, orig_values):
        """Return true if the items exists."""
        return bool(self.odoo_find(values, orig_values))

    def update_translations(self, odoo_record, translatable, ctx=None):
        """Write translations on given record."""
        ctx = ctx or {}
        for lang, values in translatable.items():
            odoo_record.with_context(lang=lang, **self.write_context()).write(
                values.copy()
            )

    def odoo_pre_create(self, values, orig_values):
        """Do some extra stuff before creating a missing record."""
        pass

    def odoo_post_create(self, odoo_record, values, orig_values):
        """Do some extra stuff after creating a missing record."""
        pass

    def create_context(self):
        """Inject context variables on create."""
        return dict(
            self.importer._odoo_create_context(),
            # mark each action w/ this flag
            connector_importer_session=True,
        )

    def odoo_create(self, values, orig_values):
        """Create a new odoo record."""
        self.odoo_pre_create(values, orig_values)
        # TODO: remove keys that are not model's fields
        odoo_record = self.model.with_context(**self.create_context()).create(
            values.copy()
        )
        # force uid
        if self.override_create_uid and values.get("create_uid"):
            self._force_value(odoo_record, values, "create_uid")
        # force create date
        if self.override_create_date and values.get("create_date"):
            self._force_value(odoo_record, values, "create_date")
        self.odoo_post_create(odoo_record, values, orig_values)
        translatable = self.importer.collect_translatable(values, orig_values)
        self.update_translations(odoo_record, translatable)
        # Set the external ID if necessary
        if self.unique_key_is_xmlid:
            external_id = values[self.unique_key]
            if not self.env.ref(external_id, raise_if_not_found=False):
                module, id_ = external_id.split(".", 1)
                self.env["ir.model.data"].create(
                    {
                        "name": id_,
                        "module": module,
                        "model": odoo_record._name,
                        "res_id": odoo_record.id,
                        "noupdate": False,
                    }
                )
        return odoo_record

    def odoo_pre_write(self, odoo_record, values, orig_values):
        """Do some extra stuff before updating an existing object."""
        pass

    def odoo_post_write(self, odoo_record, values, orig_values):
        """Do some extra stuff after updating an existing object."""
        pass

    def write_context(self):
        """Inject context variables on write."""
        return dict(
            self.importer._odoo_write_context(),
            # mark each action w/ this flag
            connector_importer_session=True,
        )

    def odoo_write(self, values, orig_values):
        """Update an existing odoo record."""
        # pass context here to be applied always on retrieved record
        odoo_record = self.odoo_find(values, orig_values).with_context(
            **self.write_context()
        )
        self.odoo_pre_write(odoo_record, values, orig_values)
        # TODO: remove keys that are not model's fields
        odoo_record.write(values.copy())
        # force uid
        if self.override_write_uid and values.get("write_uid"):
            self._force_value(odoo_record, values, "write_uid")
        # force create date
        if self.override_create_date and values.get("create_date"):
            self._force_value(odoo_record, values, "create_date")
        self.odoo_post_write(odoo_record, values, orig_values)
        translatable = self.importer.collect_translatable(values, orig_values)
        self.update_translations(odoo_record, translatable)
        return odoo_record

    def _force_value(self, record, values, fname):
        # the query construction is not vulnerable to SQL injection, as we are
        # replacing the table and column names here.
        # pylint: disable=sql-injection
        query = "UPDATE {} SET {} = %s WHERE id = %s".format(record._table, fname)
        self.env.cr.execute(query, (values[fname], record.id))
        record.invalidate_cache([fname])
