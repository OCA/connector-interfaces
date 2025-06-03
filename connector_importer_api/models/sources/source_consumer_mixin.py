# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ImportSourceConsumerApiMixin(models.AbstractModel):
    _inherit = "import.source.consumer.mixin"

    @api.model
    def _selection_source_ref_id(self):
        result = super()._selection_source_ref_id()
        result.append(("import.source.api", "API"))
        return result
