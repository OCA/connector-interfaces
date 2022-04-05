# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_importer.utils.mapper_utils import xmlid_to_rel


class ProductProductMapper(Component):
    _name = "product.product.mapper"
    _inherit = "importer.base.mapper"
    _apply_on = "product.product"

    direct = [
        # "id" needs to be in the mapped values to be converted as XML-ID
        # TODO: need to allow the use of fake destination fields like '_xmlid'
        # in direct mapping here:
        # https://github.com/OCA/connector/blob/13.0/connector/components/mapper.py#L891
        ("id", "id"),
        ("name", "name"),
        ("default_code", "default_code"),
        ("barcode", "barcode"),
        ("list_price", "list_price"),
        ("standard_price", "standard_price"),
        ("type", "type"),
        (xmlid_to_rel("uom_id"), "uom_id"),
        (xmlid_to_rel("categ_id"), "categ_id"),
    ]
    required = {"categ_id": "categ_id"}
    translatable = ["name"]

    @mapping
    def product_tmpl_id(self, record):
        if record.get("template_default_code"):
            template = self.env.ref(
                record["template_default_code"], raise_if_not_found=False
            )
            # If no product.template is found, it'll be created automatically
            # as usual when the product.product is created.Then the importer
            # will set its External ID.
            if template:
                return {"product_tmpl_id": template.id}
        return {}
