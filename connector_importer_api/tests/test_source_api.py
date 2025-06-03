# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import ValidationError

from .test_connector_importer_api_common import TestConnectorImporterApiBase


class TestSourceApi(TestConnectorImporterApiBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_compute_name(self):
        with patch.object(type(self.source_import_api), "_source_type", new="api"):
            self.source_import_api.name = False
            self.source_import_api._compute_name()
            self.assertEqual(self.source_import_api.name, "SOURCE API")

            result = self.source_import_api._config_summary_fields
            self.assertEqual(result, self.summary_fields)

            result = self.source_import_api.get_config_view_id()
            self.assertEqual(result, self.connector_api_view.id)

    def test_compute_field_ids(self):
        field_ids = [
            field.id
            for field in self.source_import_api.model_id.field_id
            if field.ttype == "char" and "token" in field.name
        ]
        self.source_import_api._compute_field_ids()
        self.assertEqual(self.source_import_api.field_ids.ids, field_ids)

    def test_get_eval(self):
        result = self.source_import_api._get_eval_context(eval_context={"test": "test"})
        self.assertIn("test", result)
        self.assertEqual(result["test"], "test")

        result = self.source_import_api._get_eval_value(eval_variables={"model_id": 10})
        self.assertIn("model_id", result)
        self.assertEqual(result["model_id"], 10)

        result = self.source_import_api._check_result_eval("test")
        self.assertIsNone(result)

        result = self.source_import_api._check_eval_code("test")
        self.assertIsNone(result)

    def test_get_eval_code(self):
        result = self.source_import_api._get_eval_code()
        self.assertEqual(
            result,
            f"result = env['res.company']"
            f".with_company({self.company_test.id})"
            f".search([('vat', '=', 'VAT123TEST')],limit=1)",
        )

    def test_get_headers(self):
        with patch.object(
            type(self.source_import_api), "_get_token", return_value="TEST_TOKEN"
        ):
            result = self.source_import_api._get_headers()
            self.assertIn("Authorization", result)
            self.assertEqual(result["Authorization"], "Bearer TEST_TOKEN")
            self.assertEqual(result["TEST_NAME"], "TEST_VALUE")
            self.assertEqual(result["TEST_NAME1"], "TEST_VALUE1")
            self.assertEqual(len(result), 3)

    def test_python_expr(self):
        with self.assertRaises(ValidationError):
            self.SourceImportApi._test_python_expr("11A", "eval")
        result = self.SourceImportApi._test_python_expr("1 + 1", "eval")
        self.assertTrue(result)
