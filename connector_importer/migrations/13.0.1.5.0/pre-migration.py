# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tools.sql import drop_not_null

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Drop import.type.settings contraint")
    drop_not_null(cr, "import_type", "settings")
