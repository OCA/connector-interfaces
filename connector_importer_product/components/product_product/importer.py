# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component

from ...utils import sanitize_external_id


class ProductProductRecordImporter(Component):
    _name = "product.product.importer"
    _inherit = ["common.product.importer"]
    _apply_on = "product.product"
    odoo_unique_key = "id"
    odoo_unique_key_is_xmlid = True

    def prepare_line(self, line):
        res = super().prepare_line(line)
        res["id"] = sanitize_external_id(line["id"])
        res["template_default_code"] = sanitize_external_id(
            line["template_default_code"]
        )
        res["categ_id"] = sanitize_external_id(line["categ_id"])
        return res
