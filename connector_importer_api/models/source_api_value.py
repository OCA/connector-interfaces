# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SourceApiValue(models.Model):
    _name = "source.api.value"
    _inherit = ["connector.importer.api.mixin"]
    _description = "Source API value"

    name = fields.Char(string="Key", required=True)
    value = fields.Char()
    eval_value = fields.Text(
        default=lambda self: self._get_default_code(), string="Value"
    )
    description = fields.Char()
    source_api_params_id = fields.Many2one("import.source.api")
    source_api_header_id = fields.Many2one("import.source.api")

    def _get_eval_context(self, eval_context=None):
        return {"self": self} | (eval_context or {})

    def _get_default_code(self):
        return ""

    def _eval_value(self, eval_context=None):
        return self._eval_source(
            eval_code=self.eval_value, mode_eval="eval", eval_context=eval_context
        )

    @api.constrains("eval_value")
    def _check_eval_value(self):
        for source in self:
            source._test_python_expr(source.eval_value.strip(), "eval")
