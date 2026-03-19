# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from textwrap import dedent

from odoo.tools import mute_logger

from .common import TestImporterBase

LOGGERS_TO_MUTE = (
    "[importer]",
    "odoo.addons.queue_job.utils",
)


class TestRecordImporterJson(TestImporterBase):
    @classmethod
    def _setup_records(cls):
        res = super()._setup_records()
        cls.import_type = cls.env["import.type"].create(
            {
                "name": "Fake Product JSON Importer",
                "key": "fake.product.json",
                "options": dedent(
                    """
                    - model: product.product
                      options:
                        importer:
                          name: importer.record
                          odoo_unique_key: default_code
                          override_existing: false
                          break_on_error: true
                        mapper:
                          name: importer.mapper.dynamic
                    """
                ),
            }
        )
        cls.recordset = cls.env["import.recordset"].create(
            {"backend_id": cls.backend.id, "import_type_id": cls.import_type.id}
        )
        cls.record = cls.env["import.record"].create({"recordset_id": cls.recordset.id})
        cls.analytic_plan = cls.env["account.analytic.plan"].create(
            {"name": "Importer JSON Plan"}
        )
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {
                "name": "Importer JSON Account",
                "plan_id": cls.analytic_plan.id,
            }
        )
        return res

    @mute_logger(*LOGGERS_TO_MUTE)
    def test_import_product_analytic_distribution_json(self):
        analytic_distribution = {str(self.analytic_account.id): 100.0}
        self.record.set_data(
            [
                {
                    "default_code": "JSON-PRODUCT-001",
                    "name": "JSON Product",
                    "analytic_distribution": json.dumps(analytic_distribution),
                }
            ]
        )

        res = self.record.run_import()

        self.assertEqual(
            res,
            {
                "product.product": {
                    "created": 1,
                    "errored": 0,
                    "updated": 0,
                    "skipped": 0,
                }
            },
        )
        product = self.env["product.product"].search(
            [("default_code", "=", "JSON-PRODUCT-001")], limit=1
        )
        self.assertTrue(product)
        self.assertEqual(product.analytic_distribution, analytic_distribution)

    @mute_logger(*LOGGERS_TO_MUTE)
    def test_import_product_analytic_distribution_python_literal(self):
        analytic_distribution = {str(self.analytic_account.id): 100.0}
        self.record.set_data(
            [
                {
                    "default_code": "JSON-PRODUCT-002",
                    "name": "JSON Product Python Literal",
                    "analytic_distribution": str(analytic_distribution),
                }
            ]
        )

        res = self.record.run_import()

        self.assertEqual(
            res,
            {
                "product.product": {
                    "created": 1,
                    "errored": 0,
                    "updated": 0,
                    "skipped": 0,
                }
            },
        )
        product = self.env["product.product"].search(
            [("default_code", "=", "JSON-PRODUCT-002")], limit=1
        )
        self.assertTrue(product)
        self.assertEqual(product.analytic_distribution, analytic_distribution)
