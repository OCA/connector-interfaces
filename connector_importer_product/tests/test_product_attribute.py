# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.tests.common import RecordCapturer
from odoo.tools import mute_logger

from .common import TestImportProductBase


class TestProduct(TestImportProductBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.importer_load_file(
            "connector_importer_product.demo_import_source_csv_product_attribute",
            "product_attribute.csv",
        )
        cls.recordset = cls.env.ref(
            "connector_importer_product.demo_import_recordset_product_attribute"
        )
        cls.env["res.lang"].with_context(active_test=False).search(
            [("code", "in", ("fr_FR", "it_IT"))]
        ).active = True

    @mute_logger("[importer]")
    def test_attribute(self):
        records = []
        with RecordCapturer(self.env["product.attribute"].sudo(), []) as capt:
            self.recordset.run_import()
            records = capt.records

        self.assertEqual(len(records), 3)
        # xids were generated
        expected = (
            self.env.ref("__setup__.product_attr_test1")
            + self.env.ref("__setup__.product_attr_test2")
            + self.env.ref("__setup__.product_attr_test3")
        )
        self.assertEqual(records.ids, expected.ids)
        self.assertRecordValues(
            expected,
            [
                {
                    "name": "TEST_1",
                    "create_variant": "always",
                    "display_type": "select",
                },
                {
                    "name": "TEST_2",
                    "create_variant": "always",
                    "display_type": "radio",
                },
                {
                    "name": "TEST_3",
                    "create_variant": "always",
                    "display_type": "radio",
                },
            ],
        )
        self.assertRecordValues(
            expected.with_context(lang="fr_FR"),
            [
                {
                    "name": "TEST_1 FR",
                },
                {
                    "name": "TEST_2 FR",
                },
                {
                    "name": "TEST_3 FR",
                },
            ],
        )
        self.assertRecordValues(
            expected.with_context(lang="it_IT"),
            [
                {
                    "name": "TEST_1 IT",
                },
                {
                    "name": "TEST_2 IT",
                },
                {
                    "name": "TEST_3 IT",
                },
            ],
        )
