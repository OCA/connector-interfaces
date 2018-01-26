# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import AbstractComponent


class OdooRecordHandler(AbstractComponent):
    """Interact w/ odoo importable records."""

    _name = 'importer.odoorecord.handler'
    _inherit = 'importer.base.component'
    _usage = 'odoorecord.handler'

    unique_key = ''
    importer = None

    def _init_handler(self, importer=None, unique_key=None):
        self.importer = importer
        self.unique_key = unique_key

    def odoo_find_domain(self, values, orig_values):
        """Domain to find the record in odoo."""
        return [(self.unique_key, '=', values[self.unique_key])]

    def odoo_find(self, values, orig_values):
        """Find any existing item in odoo."""
        item = self.model.search(
            self.odoo_find_domain(values, orig_values),
            order='create_date desc', limit=1)
        return item

    def odoo_exists(self, values, orig_values):
        """Return true if the items exists."""
        return bool(self.odoo_find(values, orig_values))

    def update_translations(self, odoo_record, translatable, ctx=None):
        """Write translations on given record."""
        ctx = ctx or {}
        for lang, values in translatable.items():
            odoo_record.with_context(
                lang=lang, **self.write_context()).write(values)

    def odoo_pre_create(self, values, orig_values):
        """Do some extra stuff before creating a missing record."""
        pass

    def odoo_post_create(self, odoo_record, values, orig_values):
        """Do some extra stuff after creating a missing record."""
        pass

    def create_context(self):
        """Inject context variables on create."""
        return {}

    def odoo_create(self, values, orig_values):
        """Create a new odoo record."""
        self.odoo_pre_create(values, orig_values)
        # TODO: remove keys that are not model's fields
        odoo_record = self.model.with_context(
            **self.create_context()).create(values)
        self.odoo_post_create(odoo_record, values, orig_values)
        translatable = self.importer.collect_translatable(values, orig_values)
        self.update_translations(odoo_record, translatable)
        return odoo_record

    def odoo_pre_write(self, odoo_record, values, orig_values):
        """Do some extra stuff before updating an existing object."""
        pass

    def odoo_post_write(self, odoo_record, values, orig_values):
        """Do some extra stuff after updating an existing object."""
        pass

    def write_context(self):
        """Inject context variables on write."""
        return {}

    def odoo_write(self, values, orig_values):
        """Update an existing odoo record."""
        # TODO: add a checkpoint? log something?
        odoo_record = self.odoo_find(values, orig_values)
        self.odoo_pre_write(odoo_record, values, orig_values)
        # TODO: remove keys that are not model's fields
        odoo_record.with_context(**self.write_context()).write(values)
        self.odoo_post_write(odoo_record, values, orig_values)
        translatable = self.importer.collect_translatable(values, orig_values)
        self.update_translations(odoo_record, translatable)
        return odoo_record
