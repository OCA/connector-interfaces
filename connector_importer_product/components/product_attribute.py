# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

from ..utils import sanitize_external_id


class ProductAttributeRecordImporter(Component):
    _name = "product.attribute.importer"
    _inherit = ["common.product.importer"]
    _apply_on = "product.attribute"
    odoo_unique_key = "id"
    odoo_unique_key_is_xmlid = True

    def prepare_line(self, line):
        res = super().prepare_line(line)
        res["id"] = sanitize_external_id(line["id"])
        return res


class ProductAttributeMapper(Component):
    _name = "product.attribute.mapper"
    _inherit = "importer.base.mapper"
    _apply_on = "product.attribute"

    direct = [
        # "id" needs to be in the mapped values to be converted as XML-ID
        # TODO: need to allow the use of fake destination fields like '_xmlid'
        # in direct mapping here:
        # https://github.com/OCA/connector/blob/13.0/connector/components/mapper.py#L891
        ("id", "id"),
        ("name", "name"),
        ("sequence", "sequence"),
    ]
    translatable = ["name"]

    @mapping
    def create_variant(self, record):
        if record.get("create_variant"):
            return {"create_variant": record["create_variant"].lower()}
        return {"create_variant": False}

    @mapping
    def display_type(self, record):
        if record.get("display_type"):
            return {"display_type": record["display_type"].lower()}
        return {"display_type": False}
