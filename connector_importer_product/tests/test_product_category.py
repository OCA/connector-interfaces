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
            "connector_importer_product.demo_import_source_csv_product_category",
            "product_category.csv",
        )
        cls.recordset = cls.env.ref(
            "connector_importer_product.demo_import_recordset_product_category"
        )

    @mute_logger("[importer]")
    def test_category(self):
        records = []
        with RecordCapturer(self.env["product.category"].sudo(), []) as capt:
            self.recordset.run_import()
            records = capt.records

        self.assertEqual(len(records), 3)
        # xids were generated
        expected = (
            self.env.ref("__setup__.product_cat_test1")
            + self.env.ref("__setup__.product_cat_test2")
            + self.env.ref("__setup__.product_cat_test3")
        )
        self.assertEqual(records.ids, expected.ids)
        self.assertRecordValues(
            expected,
            [
                {
                    "name": "TEST_1",
                    "parent_id": False,
                },
                {
                    "name": "TEST_2",
                    "parent_id": expected[0].id,
                },
                {
                    "name": "TEST_3",
                    "parent_id": expected[1].id,
                },
            ],
        )
