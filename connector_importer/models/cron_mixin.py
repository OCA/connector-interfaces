# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class CronMixin(models.AbstractModel):
    """Add cron-related features to your models.

    On inheriting models you can:

    * enable cron mode
    * configure a cron
    * save and get a specific cron to run something on your model

    You have to implement the method `run_cron`.
    """

    _name = "cron.mixin"
    _description = "Cron Mixin"

    cron_mode = fields.Boolean("Cron mode?")
    cron_start_date = fields.Datetime("Start date")
    cron_interval_number = fields.Integer("Interval number")
    cron_interval_type = fields.Selection(
        selection="_select_interval_type", string="Interval type"
    )
    cron_id = fields.Many2one(
        "ir.cron",
        string="Related cron",
        domain=lambda self: [
            ("model_id", "=", self.env["ir.model"]._get_id(self._name))
        ],
    )

    @api.model
    def _select_interval_type(self):
        return [
            ("hours", "Hours"),
            ("work_days", "Work Days"),
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
        ]

    @api.model
    def get_cron_vals(self):
        model_id = self.env["ir.model"]._get_id(self._name)
        return {
            "name": "Cron for import backend %s" % self.name,
            "model_id": model_id,
            "state": "code",
            "code": "model.run_cron(%d)" % self.id,
            "interval_number": self.cron_interval_number,
            "interval_type": self.cron_interval_type,
            "nextcall": self.cron_start_date,
        }

    def _update_or_create_cron(self):
        """Update or create cron record if needed."""
        if self.cron_mode:
            cron_model = self.env["ir.cron"]
            cron_vals = self.get_cron_vals()
            if not self.cron_id:
                self.cron_id = cron_model.create(cron_vals)
            else:
                self.cron_id.write(cron_vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._update_or_create_cron()
        return records

    def write(self, vals):
        res = super().write(vals)
        for backend in self:
            backend._update_or_create_cron()
        return res

    @api.model
    def run_cron(self):
        raise NotImplementedError()
