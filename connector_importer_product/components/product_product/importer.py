# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class ProductProductRecordImporter(Component):
    _name = "product.product.importer"
    _inherit = ["common.product.importer"]
    _apply_on = "product.product"
    _mapper_name = "product.product.mapper"
    odoo_unique_key = "default_code"
    # _break_on_error = True
