# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64
import logging

# import os
from pathlib import Path

from odoo.tests import tagged

from odoo.addons.component.tests.common import TransactionComponentCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestImportProductBase(TransactionComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.backend = cls.env.ref("connector_importer_product.demo_import_backend")
        cls.backend.debug_mode = True  # synchronous jobs

    @classmethod
    def importer_load_file(cls, src_external_id, csv_filename):
        csv_path = Path(__file__).parent / "data" / csv_filename
        _logger.info("Loading '%s' file to '%s'...", csv_path, src_external_id)
        source = cls.env.ref(src_external_id)
        with open(csv_path, "rb") as csv_file:
            csv_content = csv_file.read()
            b64_content = base64.b64encode(csv_content)
            source.write({"csv_file": b64_content, "csv_filename": csv_filename})

    @classmethod
    def importer_run(cls, external_id):
        recordset = cls.env.ref(external_id)
        recordset.run_import()
