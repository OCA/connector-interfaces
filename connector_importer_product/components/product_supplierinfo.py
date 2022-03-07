# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component

from ..utils import sanitize_external_id


class ProductSupplierinfoImporter(Component):
    _name = "product.supplierinfo.importer"
    _inherit = ["common.product.importer", "importer.record.csv.std"]
    _apply_on = "product.supplierinfo"
    _use_xmlid = False

    def prepare_line(self, line):
        res = super().prepare_line(line)
        for key in line.keys():
            if key == "id" or key.endswith("/id"):
                res[key] = sanitize_external_id(line[key])
        return res
