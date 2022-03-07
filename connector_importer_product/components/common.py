# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class CommonProductImporter(Component):
    _name = "common.product.importer"
    _inherit = "importer.record"
