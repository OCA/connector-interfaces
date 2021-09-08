# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ImportSourceConsumerMixin(models.AbstractModel):
    """Source consumer mixin.

    Inheriting models can setup, configure and use import sources.

    Relation towards source records is generic to grant maximum freedom
    on which source type to use.
    """

    _name = "import.source.consumer.mixin"
    _description = "Import source consumer"

    source_id = fields.Integer(string="Source ID", required=False)
    source_model = fields.Selection(
        string="Source type", selection="_selection_source_ref_id"
    )
    source_ref_id = fields.Reference(
        string="Source",
        compute="_compute_source_ref_id",
        selection="_selection_source_ref_id",
        # NOTE: do not store a computed fields.Reference, Odoo crashes
        # with an error message "Mixing appels and orange..." when performing
        # a self.recompute() on such fields.
        store=False,
    )
    source_config_summary = fields.Html(
        compute="_compute_source_config_summary", readonly=True
    )

    @api.depends("source_model", "source_id")
    def _compute_source_ref_id(self):
        for item in self:
            item.source_ref_id = False
            if not item.source_id or not item.source_model:
                continue
            item.source_ref_id = "{0.source_model},{0.source_id}".format(item)

    @api.model
    def _selection_source_ref_id(self):
        return [("import.source.csv", "CSV"), ("import.source.csv.std", "Odoo CSV")]

    @api.depends("source_ref_id")
    def _compute_source_config_summary(self):
        for item in self:
            item.source_config_summary = False
            if not item.source_ref_id:
                continue
            item.source_config_summary = item.source_ref_id.config_summary

    def open_source_config(self):
        self.ensure_one()
        action = self.env[self.source_model].get_formview_action()
        action.update(
            {
                "views": [(self.env[self.source_model].get_config_view_id(), "form")],
                "res_id": self.source_id,
                "target": "new",
            }
        )
        return action

    def get_source(self):
        """Return the source to the consumer."""
        return self.source_ref_id
