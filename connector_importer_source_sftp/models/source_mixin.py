# Copyright 2019 Camptocamp SA (<http://camptocamp.com>)
# @author: Sebastien Alix <sebastien.alix@camptocamp.com>
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, models


class ImportSourceConsumerMixin(models.AbstractModel):
    _inherit = "import.source.consumer.mixin"

    @api.model
    def _selection_source_ref_id(self):
        selection = super()._selection_source_ref_id()
        new_source = ("import.source.csv.sftp", "CSV SFTP")
        if new_source not in selection:
            selection.append(new_source)
        return selection
