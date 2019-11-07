# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class OdooRecordHandlerCSVStd(Component):
    """Interact w/ odoo importable records from standard Odoo CSV files."""

    _name = "importer.odoorecord.handler.csv.std"
    _inherit = "importer.odoorecord.handler"
    _usage = "odoorecord.handler.csv"
    xmlid_key = "id"  # CSV field containing the record XML-ID

    def odoo_find(self, values, orig_values, use_xmlid=False):
        """Find any existing item in odoo based on the XML-ID."""
        if use_xmlid:
            if not self.xmlid_key:
                return self.model
            item = self.env.ref(values[self.xmlid_key], raise_if_not_found=False)
            return item
        return super().odoo_find(values, orig_values)

    def odoo_exists(self, values, orig_values, use_xmlid=False):
        """Return true if the items exists."""
        return bool(self.odoo_find(values, orig_values, use_xmlid))

    def odoo_create(self, values, orig_values):
        """Create a new odoo record."""
        raise NotImplementedError(
            "This method is not used when importing standard CSV files."
        )

    def odoo_write(self, values, orig_values):
        """Create a new odoo record."""
        raise NotImplementedError(
            "This method is not used when importing standard CSV files."
        )
