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
            "connector_importer_product.demo_import_source_csv_product_packaging",
            "product_packaging.csv",
        )
        cls.recordset = cls.env.ref(
            "connector_importer_product.demo_import_recordset_product_packaging"
        )

    @mute_logger("[importer]")
    def test_packaging(self):
        records = []
        with RecordCapturer(self.env["product.packaging"].sudo(), []) as capt:
            self.recordset.run_import()
            records = capt.records

        self.assertEqual(len(records), 4)
        # xids were generated
        expected = (
            self.env.ref("__setup__.product_pkg_test1")
            + self.env.ref("__setup__.product_pkg_test2")
            + self.env.ref("__setup__.product_pkg_test3")
            + self.env.ref("__setup__.product_pkg_test4")
        )
        self.assertEqual(sorted(records.ids), sorted(expected.ids))
        self.assertRecordValues(
            expected,
            [
                {
                    "name": "TEST_1",
                    "product_id": False,
                    "qty": 10,
                },
                {
                    "name": "TEST_2",
                    "product_id": self.env.ref("product.product_product_3").id,
                    "qty": 8,
                },
                {
                    "name": "TEST_3",
                    "product_id": False,
                    "qty": 6,
                },
                {
                    "name": "TEST_4",
                    "product_id": False,
                    "qty": 4,
                },
            ],
        )
