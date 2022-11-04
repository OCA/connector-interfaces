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
        cls.recordset_att = cls.env.ref(
            "connector_importer_product.demo_import_recordset_product_attribute"
        )
        cls.importer_load_file(
            "connector_importer_product.demo_import_source_csv_product_attribute_value",
            "product_attribute_value.csv",
        )
        cls.recordset_att_value = cls.env.ref(
            "connector_importer_product.demo_import_recordset_product_attribute_value"
        )
        cls.env["res.lang"].with_context(active_test=False).search(
            [("code", "in", ("fr_FR", "it_IT"))]
        ).active = True

    @mute_logger("[importer]")
    def test_attribute(self):
        records = []
        with RecordCapturer(self.env["product.attribute"].sudo(), []) as capt:
            self.recordset_att.run_import()
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

    @mute_logger("[importer]")
    def test_attribute_value(self):
        self.recordset_att.run_import()
        records = []
        with RecordCapturer(self.env["product.attribute.value"].sudo(), []) as capt:
            self.recordset_att_value.run_import()
            records = capt.records

        self.assertEqual(len(records), 12)
        # xids were generated
        expected = (
            self.env.ref("__setup__.product_attr_value_test1_value1")
            + self.env.ref("__setup__.product_attr_value_test1_value2")
            + self.env.ref("__setup__.product_attr_value_test1_value3")
            + self.env.ref("__setup__.product_attr_value_test1_value4")
            + self.env.ref("__setup__.product_attr_value_test2_value1")
            + self.env.ref("__setup__.product_attr_value_test2_value2")
            + self.env.ref("__setup__.product_attr_value_test2_value3")
            + self.env.ref("__setup__.product_attr_value_test2_value4")
            + self.env.ref("__setup__.product_attr_value_test3_value1")
            + self.env.ref("__setup__.product_attr_value_test3_value2")
            + self.env.ref("__setup__.product_attr_value_test3_value3")
            + self.env.ref("__setup__.product_attr_value_test3_value4")
        )
        self.assertEqual(records.ids, expected.ids)
        self.assertRecordValues(
            expected,
            [
                {
                    "name": "VALUE_1_1",
                    "attribute_id": self.env.ref("__setup__.product_attr_test1").id,
                },
                {
                    "name": "VALUE_1_2",
                    "attribute_id": self.env.ref("__setup__.product_attr_test1").id,
                },
                {
                    "name": "VALUE_1_3",
                    "attribute_id": self.env.ref("__setup__.product_attr_test1").id,
                },
                {
                    "name": "VALUE_1_4",
                    "attribute_id": self.env.ref("__setup__.product_attr_test1").id,
                },
                {
                    "name": "VALUE_2_1",
                    "attribute_id": self.env.ref("__setup__.product_attr_test2").id,
                },
                {
                    "name": "VALUE_2_2",
                    "attribute_id": self.env.ref("__setup__.product_attr_test2").id,
                },
                {
                    "name": "VALUE_2_3",
                    "attribute_id": self.env.ref("__setup__.product_attr_test2").id,
                },
                {
                    "name": "VALUE_2_4",
                    "attribute_id": self.env.ref("__setup__.product_attr_test2").id,
                },
                {
                    "name": "VALUE_3_1",
                    "attribute_id": self.env.ref("__setup__.product_attr_test3").id,
                },
                {
                    "name": "VALUE_3_2",
                    "attribute_id": self.env.ref("__setup__.product_attr_test3").id,
                },
                {
                    "name": "VALUE_3_3",
                    "attribute_id": self.env.ref("__setup__.product_attr_test3").id,
                },
                {
                    "name": "VALUE_3_4",
                    "attribute_id": self.env.ref("__setup__.product_attr_test3").id,
                },
            ],
        )
        self.assertRecordValues(
            expected.with_context(lang="fr_FR"),
            [
                {"name": "VALUE_1_1 FR"},
                {"name": "VALUE_1_2 FR"},
                {"name": "VALUE_1_3 FR"},
                {"name": "VALUE_1_4 FR"},
                {"name": "VALUE_2_1 FR"},
                {"name": "VALUE_2_2 FR"},
                {"name": "VALUE_2_3 FR"},
                {"name": "VALUE_2_4 FR"},
                {"name": "VALUE_3_1 FR"},
                {"name": "VALUE_3_2 FR"},
                {"name": "VALUE_3_3 FR"},
                {"name": "VALUE_3_4 FR"},
            ],
        )
        self.assertRecordValues(
            expected.with_context(lang="it_IT"),
            [
                {"name": "VALUE_1_1 IT"},
                {"name": "VALUE_1_2 IT"},
                {"name": "VALUE_1_3 IT"},
                {"name": "VALUE_1_4 IT"},
                {"name": "VALUE_2_1 IT"},
                {"name": "VALUE_2_2 IT"},
                {"name": "VALUE_2_3 IT"},
                {"name": "VALUE_2_4 IT"},
                {"name": "VALUE_3_1 IT"},
                {"name": "VALUE_3_2 IT"},
                {"name": "VALUE_3_3 IT"},
                {"name": "VALUE_3_4 IT"},
            ],
        )
