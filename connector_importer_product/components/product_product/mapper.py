# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_importer.utils.mapper_utils import backend_to_rel


class ProductProductMapper(Component):
    _name = "product.product.mapper"
    # Non mapped fields will be managed by the dynamic mapper
    _inherit = "importer.mapper.dynamic"
    _apply_on = "product.product"
    _mapper_usage = "importer.mapper"

    direct = [
        (
            backend_to_rel(
                "tmpl_default_code",
                # When you want to related a template via code
                # this kind of search is mandatory
                # because Odoo will set the template.default_code to false
                # every time it has more than one variant.
                # We assume that if you are using `tmpl_default_code`
                # all the variants in your dataset either have the same code
                # or at least one of them has default_code = tmpl_default_code.
                search_field="product_variant_ids.default_code",
            ),
            "product_tmpl_id",
        ),
    ]
    required = {
        "name": "name",
    }
    translatable = ["name"]

    defaults = [("sale_ok", True)]

    @mapping
    def code(self, record):
        """Ensure there's always a default code.

        We must have a default code to univocally find the template
        if it's already created.
        In your dataset you might not care about having a default code per variant
        which means that likely you'll have only `tmpl_default_code`.
        If that's the case, we case, the 1st variant that will create the product
        and its template, won't have a default_code for it and any subsequent lookup
        of the template will fail.
        """
        vals = {}
        for key in ("default_code", "tmpl_default_code"):
            if record.get(key):
                vals["default_code"] = record[key]
                break
        return vals

    def finalize(self, map_record, values):
        res = super().finalize(map_record, values)
        # Avoid having an empty barcode which must be unique.
        # Odoo will try to store the barcode as an empty string
        # whenever is not valued: simply ignore it when it happens
        # to avoid:
        # psycopg2.errors.UniqueViolation: duplicate key value
        # violates unique constraint "product_product_barcode_uniq".
        #
        # Note: this can be achieved by using this mapper option:
        #
        # source_key_empty_skip:
        #   - barcode
        #
        # Since we have a special mapper, let's handle it here.
        if "barcode" in res and not res.get("barcode"):
            res.pop("barcode")
        return res
