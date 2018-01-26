# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SourceApiValue(models.Model):
    _name = "source.api.value"
    _description = "Source API value"

    name = fields.Char(string="Key", required=True)
    value = fields.Char(required=True)
    description = fields.Char()

    source_api_params_id = fields.Many2one("import.source.api")
    source_api_header_id = fields.Many2one("import.source.api")
