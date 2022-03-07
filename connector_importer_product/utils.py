# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _
from odoo.exceptions import UserError


def sanitize_external_id(external_id, default_mod_name="__setup__"):
    """Ensure that the external ID has dotted prefix."""
    if not external_id:
        return external_id
    id_parts = external_id.split(".", 1)
    if len(id_parts) == 2:
        if "." in id_parts[1]:
            raise UserError(
                _(
                    "The ID reference '%s' must contain maximum one dot (or 0). "
                    "They are used to refer to other modules ID, "
                    "in the form: module.record_id"
                )
                % (external_id,)
            )
    else:
        return f"{default_mod_name}.{external_id}"
    return external_id
