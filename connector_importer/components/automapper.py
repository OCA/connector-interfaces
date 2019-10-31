# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class AutoMapper(Component):
    _name = "importer.mapper.auto"
    _inherit = "importer.base.mapper"
    _usage = "importer.automapper"

    @mapping
    def auto_mapping(self, record):
        """Generate the values automatically by removing internal keys."""
        result = {k: v for k, v in record.items() if not k.startswith("_")}
        return result
