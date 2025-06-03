# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class Tracker(Component):
    _inherit = "importer.tracking.handler"

    def chunk_report_item(self, line, odoo_record=None, message="", values=None):
        return {
            "line_nr": line.get("_line_nr", False) or line.get("id", False),
            "message": message,
            "model": self.model_name,
            "odoo_record": odoo_record.id if odoo_record else None,
        }

    def _log(self, msg, line=None, level="info"):
        handler = getattr(self.logger, level)
        msg = "{prefix}{line}[model: {model}] {msg}".format(
            prefix=self.log_prefix,
            line="[line: {}]".format(
                line.get("_line_nr", False) or line.get("id", False)
            )
            if line
            else "",
            model=self.model_name,
            msg=msg,
        )
        handler(msg)
