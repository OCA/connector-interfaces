# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import odoo.tests.common as common
from odoo import Command


class TestConnectorImporterApiBase(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SourceImportApi = cls.env["import.source.api"]
        cls.IrModel = cls.env["ir.model"]
        cls.ResCompany = cls.env["res.company"]
        cls.company_test = cls.ResCompany.create(
            {
                "name": "Test Company",
                "vat": "VAT123TEST",
                "street": "Street Test",
                "city": "City Test",
                "country_id": cls.env.ref("base.be").id,
            }
        )
        cls.model_company_id = cls.IrModel.search([("model", "=", "res.company")])[0]
        cls.source_import_api = cls.SourceImportApi.create(
            {
                "name": "Test Source API",
                "enviroment": "test",
                "enviroment_url": "https://api.test.cloud",
                "type_request": "get",
                "url": "/url/test",
                "model_domain": "[('vat', '=', 'VAT123TEST')]",
                "model_id": cls.model_company_id.id,
                "company_id": cls.company_test.id,
                "header_ids": [
                    Command.create(
                        {
                            "name": "TEST_NAME",
                            "value": "TEST_VALUE",
                            "eval_value": "'TEST_VALUE'",
                        }
                    ),
                    Command.create(
                        {
                            "name": "TEST_NAME1",
                            "value": "TEST_VALUE1",
                            "eval_value": "'TEST_VALUE1'",
                        }
                    ),
                ],
                "param_ids": [
                    Command.create(
                        {
                            "name": "TEST_PARAM",
                            "eval_value": "10 +5",
                        }
                    ),
                    Command.create(
                        {
                            "name": "TEST_PARAM1",
                            "eval_value": "10",
                        }
                    ),
                ],
            }
        )
        cls.summary_fields = [
            "chunk_size",
            "company_id",
            "enviroment",
            "type_request",
            "enviroment_url",
            "url",
            "type_authorization",
        ]
        cls.connector_api_view = cls.env.ref(
            "connector_importer_api.importer_source_api_view_form"
        )
