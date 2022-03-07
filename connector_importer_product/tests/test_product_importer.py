# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64
import logging
import os

from odoo.tests import tagged
from odoo.tests.common import SavepointCase

_logger = logging.getLogger(__name__)

DIR_DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


@tagged("post_install", "-at_install")
class TestProduct(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        backend = cls.env.ref("connector_importer_product.demo_import_backend")
        backend.debug_mode = True  # synchronous jobs
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
        # Load product variants (import will be performed during tests)
        cls.importer_load_file(
            "connector_importer_product.demo_import_source_csv_product_product",
            "product_product.csv",
        )

    @classmethod
    def importer_load_file(cls, src_external_id, csv_filename):
        csv_path = os.path.join(DIR_DATA_PATH, csv_filename)
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

    def test_init_product(self):
        """Ensure that variants are not removed/recreated during the import."""
        recordset = self.env.ref(
            "connector_importer_product.demo_import_recordset_product_product"
        )
        # Ensure that the importer logged two errors
        with self.assertLogs(logger="[importer]", level="ERROR") as cm:
            recordset.run_import()
        error_messages = [err for err in cm.output if err.startswith("ERROR")]
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
        errors = recordset.report_data["product.product"]["errored"]
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
