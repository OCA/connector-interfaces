# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector_importer.utils.mapper_utils import convert, xmlid_to_rel

from ..utils import sanitize_external_id


class ProductAttributeValueRecordImporter(Component):
    _name = "product.attribute.value.importer"
    _inherit = ["common.product.importer"]
    _apply_on = "product.attribute.value"
    odoo_unique_key = "id"
    # FIXME: we should be able to use `name` as unique key
    # and pass the key to be used for the XID to be added in odoorecordhandler.
    odoo_unique_key_is_xmlid = True

    def prepare_line(self, line):
        res = super().prepare_line(line)
        res["id"] = sanitize_external_id(line["id"])
        res["attribute_id/id"] = sanitize_external_id(line["attribute_id/id"])
        return res


class ProductAttributeValueMapper(Component):
    _name = "product.attribute.value.mapper"
    _inherit = "importer.base.mapper"
    _apply_on = "product.attribute.value"

    direct = [
        # "id" needs to be in the mapped values to be converted as XML-ID
        # TODO: need to allow the use of fake destination fields like '_xmlid'
        # in direct mapping here:
        # https://github.com/OCA/connector/blob/13.0/connector/components/mapper.py#L891
        ("id", "id"),
        ("name", "name"),
        ("sequence", "sequence"),
        ("html_color", "html_color"),
        (convert("is_custom", "bool"), "is_custom"),
        (xmlid_to_rel("attribute_id/id"), "attribute_id"),
    ]
    translatable = ["name"]
    required = {"attribute_id/id": "attribute_id"}
