# Author: Simone Orsi
# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging

from odoo import _
from odoo.exceptions import UserError
from odoo.tools import DotDict

_logger = logging.getLogger(__file__)


def get_importer_for_config(backend, work_on_model, importer_config, **work_on_kw):
    """Retrieve importer component for given backend, model and configuration."""
    # When using jobs, importer_config is loaded from the DB as a pure dict.
    # Make sure we always have a dotted dict.
    # FIXME: we should pass the import_type_id to the job and load it here.
    importer_config = DotDict(importer_config)
    work_on_kw.update(
        {
            "options": importer_config.options,
        }
    )
    with backend.with_context(**importer_config.context).work_on(
        importer_config.model, **work_on_kw
    ) as work:
        importer_name = importer_config.importer.name
        return work.component_by_name(importer_name)


def sanitize_external_id(external_id, default_mod_name=None):
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
        default_mod_name = default_mod_name or "__setup__"
        return f"{default_mod_name}.{external_id}"
    return external_id


def to_b64(file_content):
    """Safe convertion to b64"""
    try:
        # py > 3.9
        return base64.encodestring(file_content)
    except AttributeError:
        # py <= 3.9
        return base64.b64encode(file_content)
