# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_importer.utils.mapper_utils import backend_to_rel
from odoo.addons.connector_importer.utils.misc import sanitize_external_id


class ProductSupplierinfoMapper(Component):
    _name = "product.supplierinfo.mapper"
    # Non mapped fields will be managed by the dynamic mapper
    _inherit = "importer.mapper.dynamic"
    _apply_on = "product.supplierinfo"
    _usage = "importer.mapper"

    required = {
        "__name": "partner_id",
        "__tmpl": "product_tmpl_id",
    }

    @mapping
    def product_tmpl_id(self, record):
        """Ensure a template is found."""
        # TODO: add test
        value = None
        if record.get("tmpl_default_code"):
            handler = backend_to_rel(
                "tmpl_default_code",
                # See motiviation in product_product.mapper.
                search_field="product_variant_ids.default_code",
            )
            value = handler(record, "product_tmpl_id")
        elif record.get("xid::product_tmpl_id"):
            # Special case for when products are univocally identified via xid.
            # TODO: try to get rid of this
            # by allowing to specify backend_to_rel options via conf
            tmpl_xid = sanitize_external_id(record.get("xid::product_tmpl_id"))
            rec = self.env.ref(tmpl_xid, raise_if_not_found=False)
            value = rec.id if rec else None
        return {"product_tmpl_id": value}


class ProductSupplierinfoRecordHandler(Component):
    """Interact w/ odoo importable records."""

    _name = "product.supplierinfo.handler"
    _inherit = "importer.odoorecord.handler"
    _apply_on = "product.supplierinfo"

    def odoo_find_domain(self, values, orig_values):
        domain = [
            (self.unique_key, "=", values[self.unique_key]),
            ("product_tmpl_id", "=", values["product_tmpl_id"]),
        ]
        for key in ("product_id",):
            if values.get("product_id"):
                domain.append((key, "=", values[key]))
        return domain
