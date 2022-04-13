# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector_importer.utils.mapper_utils import backend_to_rel


class ProductSupplierinfoMapper(Component):
    _name = "product.supplierinfo.mapper"
    # Non mapped fields will be managed by the dynamic mapper
    _inherit = "importer.mapper.dynamic"
    _apply_on = "product.supplierinfo"
    _usage = "importer.mapper"

    direct = [
        (
            backend_to_rel(
                "tmpl_default_code",
                # See motiviation in product_product.mapper.
                search_field="product_variant_ids.default_code",
            ),
            "product_tmpl_id",
        ),
    ]
    required = {
        "__name": "name",
        "__tmpl": "product_tmpl_id",
    }

    # TODO: set partner supplier rank


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
