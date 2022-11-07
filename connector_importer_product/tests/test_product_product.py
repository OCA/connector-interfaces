# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import RecordCapturer
from odoo.tools import mute_logger

from .common import TestImportProductBase


class TestProduct(TestImportProductBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load and import product attributes
        cls.importer_load_file(
            "connector_importer_product.demo_import_source_csv_product_attribute",
            "product_attribute.csv",
        )
        cls.importer_run(
            "connector_importer_product.demo_import_recordset_product_attribute"
        )
        # Load and import product attribute values
        cls.importer_load_file(
            "connector_importer_product.demo_import_source_csv_product_attribute_value",
            "product_attribute_value.csv",
        )
        cls.importer_run(
            "connector_importer_product.demo_import_recordset_product_attribute_value"
        )
        cls.recordset = cls.env.ref(
            "connector_importer_product.demo_import_recordset_product_product"
        )

    def _test_attributes(self, records):
        # Check attribute assignation
        attr_test_1 = self.env.ref("__setup__.product_attr_test1")
        attr_test_2 = self.env.ref("__setup__.product_attr_test2")
        attr_test_3 = self.env.ref("__setup__.product_attr_test3")
        tmpl0_attr_lines = records[0].attribute_line_ids.attribute_id
        tmpl1_attr_lines = records[1].attribute_line_ids.attribute_id
        tmpl2_attr_lines = records[2].attribute_line_ids.attribute_id
        tmpl3_attr_lines = records[3].attribute_line_ids.attribute_id
        tmpl4_attr_lines = records[4].attribute_line_ids.attribute_id
        self.assertIn(attr_test_1, tmpl0_attr_lines)
        self.assertIn(attr_test_2, tmpl0_attr_lines)
        self.assertNotIn(attr_test_3, tmpl0_attr_lines)
        self.assertIn(attr_test_1, tmpl1_attr_lines)
        self.assertIn(attr_test_2, tmpl1_attr_lines)
        self.assertNotIn(attr_test_3, tmpl1_attr_lines)
        self.assertIn(attr_test_1, tmpl2_attr_lines)
        self.assertIn(attr_test_2, tmpl2_attr_lines)
        self.assertNotIn(attr_test_3, tmpl2_attr_lines)
        self.assertIn(attr_test_1, tmpl3_attr_lines)
        self.assertIn(attr_test_2, tmpl3_attr_lines)
        self.assertNotIn(attr_test_3, tmpl3_attr_lines)
        self.assertIn(attr_test_1, tmpl4_attr_lines)
        self.assertIn(attr_test_2, tmpl4_attr_lines)
        self.assertIn(attr_test_3, tmpl4_attr_lines)

        # Check attr values
        expected_attributes = {
            attr_test_1: (
                # expected value by line nr
                self.env.ref("__setup__.product_attr_value_test1_value1"),
                self.env.ref("__setup__.product_attr_value_test1_value1"),
                self.env.ref("__setup__.product_attr_value_test1_value1"),
                self.env.ref("__setup__.product_attr_value_test1_value1"),
                self.env.ref("__setup__.product_attr_value_test1_value1"),
            ),
            attr_test_2: (
                self.env.ref("__setup__.product_attr_value_test2_value1"),
                self.env.ref("__setup__.product_attr_value_test2_value1"),
                self.env.ref("__setup__.product_attr_value_test2_value1"),
                self.env.ref("__setup__.product_attr_value_test2_value2"),
                self.env.ref("__setup__.product_attr_value_test2_value3"),
            ),
            attr_test_3: (
                None,
                None,
                None,
                None,
                self.env.ref("__setup__.product_attr_value_test3_value1"),
            ),
        }
        for attr, values in expected_attributes.items():
            for i, val in enumerate(values):
                rec = records[i]
                if val is None:
                    continue
                self.assertTrue(
                    self._get_matching_attr(rec, attr, val),
                    f"{attr.name} / {val.name} does not match on {rec.name}",
                )

    @staticmethod
    def _get_matching_attr(rec, attr, val):
        return rec.product_template_attribute_value_ids.filtered(
            lambda x: x.attribute_id == attr and x.product_attribute_value_id == val
        )

    @mute_logger("[importer]")
    def test_default_code_only__different_tmpl(self):
        # Load a file that has only default codes.
        # Since we don't have any tmpl code matching, we'll get 1 tmpl+variant per line
        self.importer_load_file(
            "connector_importer_product.demo_import_source_csv_product_product",
            "product_product__default_code_only.csv",
        )
        records = []
        with RecordCapturer(self.env["product.product"].sudo(), []) as capt:
            self.recordset.run_import()
            records = capt.records.sorted("default_code")

        self.assertEqual(len(records), 5)
        # all templates are different
        self.assertEqual(len(records.mapped("product_tmpl_id")), 5)
        # Ensure minimal data is set
        self.assertRecordValues(
            records,
            [
                {
                    "name": "TEST 1.1",
                    "default_code": "VARIANT_TEST_1_1",
                    "uom_id": self.env.ref("uom.product_uom_categ_unit").id,
                    "categ_id": self.env.ref("product.product_category_all").id,
                },
                {
                    "name": "TEST 1.2",
                    "default_code": "VARIANT_TEST_1_2",
                    "uom_id": self.env.ref("uom.product_uom_categ_unit").id,
                    "categ_id": self.env.ref("product.product_category_all").id,
                },
                {
                    "name": "TEST 2.1",
                    "default_code": "VARIANT_TEST_2_1",
                    "uom_id": self.env.ref("uom.product_uom_categ_unit").id,
                    "categ_id": self.env.ref("product.product_category_all").id,
                },
                {
                    "name": "TEST 2.2",
                    "default_code": "VARIANT_TEST_2_2",
                    "uom_id": self.env.ref("uom.product_uom_categ_unit").id,
                    "categ_id": self.env.ref("product.product_category_all").id,
                },
                {
                    "name": "TEST 2.3",
                    "default_code": "VARIANT_TEST_2_3",
                    "uom_id": self.env.ref("uom.product_uom_categ_unit").id,
                    "categ_id": self.env.ref("product.product_category_all").id,
                },
            ],
        )
        # Ensure attributes are assigned properly
        self._test_attributes(records)

    @mute_logger("[importer]")
    def test_default_code_only__same_tmpl(self):
        # Load a file that has only default codes.
        # Since we don't have any tmpl code matching, we'll get 1 tmpl+variant per line
        self.importer_load_file(
            "connector_importer_product.demo_import_source_csv_product_product",
            "product_product__default_code_same_tmpl.csv",
        )
        records = []
        with RecordCapturer(self.env["product.product"].sudo(), []) as capt:
            # with self.assertLogs(logger="[importer]", level="ERROR") as log_capt:
            self.recordset.run_import()
            # self._test_errors(log_capt)
            records = capt.records.sorted("default_code")

        # Less records, because some variants are duplicated
        self.assertEqual(len(records), 3)
        # Only 2 templates
        self.assertEqual(len(records.mapped("product_tmpl_id")), 2)
        # Ensure minimal data is set
        self.assertRecordValues(
            records,
            [
                {
                    "name": "TEST 1.1",
                    "default_code": "VARIANT_TEST_1_1",
                    "uom_id": self.env.ref("uom.product_uom_categ_unit").id,
                    "categ_id": self.env.ref("product.product_category_all").id,
                },
                {
                    "name": "TEST 2.2",
                    "default_code": "VARIANT_TEST_2_1",
                    "uom_id": self.env.ref("uom.product_uom_categ_unit").id,
                    "categ_id": self.env.ref("product.product_category_all").id,
                },
                {
                    "name": "TEST 2.2",
                    "default_code": "VARIANT_TEST_2_2",
                    "uom_id": self.env.ref("uom.product_uom_categ_unit").id,
                    "categ_id": self.env.ref("product.product_category_all").id,
                },
            ],
        )
        # TODO:
        # 1. make _test_attributes work w/ this case
        # 2. add a new case for barcode
        # 3. make _test_errors work
        # Ensure attributes are assigned properly
        # self._test_attributes(records)

    def _test_errors(self, log_capt):
        error_messages = [err for err in log_capt.output if err.startswith("ERROR")]
        self.assertEqual(len(error_messages), 2)
        message_1 = (
            "ERROR:[importer]:product_product [line: 3][model: product.product] "
            "Product 'VARIANT_TEST_1_2' seems to be a duplicate of "
            "'VARIANT_TEST_1_1' (same attributes). Unable to import it."
        )
        self.assertIn(message_1, error_messages)
        message_2 = (
            "ERROR:[importer]:product_product [line: 6][model: product.product] "
            "Product 'VARIANT_TEST_2_3' has not the same attributes than "
            "'VARIANT_TEST_2_1'. Unable to import it."
        )
        self.assertIn(message_2, error_messages)
        errors = self.recordset.report_data["product.product"]["errored"]
        # [line: 2] OK
        product_test1_1 = self.env.ref("__setup__.product_test1_1")
        self.assertEqual(product_test1_1.default_code, "VARIANT_TEST_1_1")
        # [line: 3] Product 'VARIANT_TEST_1_2' seems to be a duplicate of
        # 'VARIANT_TEST_1_1' (same attributes). Unable to import it.
        product_test1_2 = self.env.ref(
            "__setup__.product_test1_2", raise_if_not_found=False
        )
        self.assertFalse(product_test1_2)
        self.assertEqual(errors[0]["line_nr"], 3)
        self.assertIn("VARIANT_TEST_1_1", errors[0]["message"])
        self.assertIn("VARIANT_TEST_1_2", errors[0]["message"])
        # [line: 4] OK
        product_test2_1 = self.env.ref("__setup__.product_test2_1")
        self.assertEqual(product_test2_1.default_code, "VARIANT_TEST_2_1")
        # [line: 5] OK
        product_test2_2 = self.env.ref("__setup__.product_test2_2")
        self.assertEqual(product_test2_2.default_code, "VARIANT_TEST_2_2")
        # [line: 6] Product 'VARIANT_TEST_2_3' has not the same attributes than
        # 'VARIANT_TEST_2_1'. Unable to import it.
        product_test2_3 = self.env.ref(
            "__setup__.product_test2_3", raise_if_not_found=False
        )
        self.assertFalse(product_test2_3)
        self.assertEqual(errors[1]["line_nr"], 6)
        self.assertIn("VARIANT_TEST_2_1", errors[1]["message"])
        self.assertIn("VARIANT_TEST_2_3", errors[1]["message"])
