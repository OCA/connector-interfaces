# Copyright 2026 ACSONE SA/NV <https://acsone.eu>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import io
import json
from unittest.mock import patch

import requests
from requests import Response

from odoo.fields import Command

from .test_connector_importer_api_common import TestConnectorImporterApiBase


class TestSourceApiPost(TestConnectorImporterApiBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.source_import_api.type_request = "post"
        cls.source_import_api.stream = True
        cls.source_import_api.type_authorization = "basic_auth"
        cls.source_import_api.params_code = {"parameter 1": {"sub 1": "value 1"}}
        cls.source_import_api.username = "test"
        cls.source_import_api.password = "test"

        cls.source_import_api.write(
            {
                "header_ids": [
                    Command.create(
                        {
                            "name": "Content-Type",
                            "value": "application/json",
                        }
                    ),
                    Command.create(
                        {
                            "name": "Accept",
                            "value": "application/x-json-stream",
                        }
                    ),
                ],
            }
        )

    def test_post_stream_call(self):
        with patch.object(requests, "post") as mock_post:
            response = Response()
            response.status_code = 200
            response._content = b'{"status": "ok"}'
            response.raw = io.BytesIO(response._content)
            response.json = lambda: {"status": "ok"}
            mock_post.return_value = response
            results = self.source_import_api._get_lines()
            for result in results:
                self.assertEqual("ok", result.get("status"))

    def test_post_call(self):
        self.source_import_api.stream = False
        with patch.object(requests, "post") as mock_post:
            response = Response()
            response.status_code = 200
            response.json = lambda: {"status": "ok"}
            mock_post.return_value = response
            results = self.source_import_api._get_lines()
            for result in results:
                self.assertEqual("ok", result.get("status"))

    def test_post_call_data(self):
        self.source_import_api.data_code = {"data": "The data"}
        self.source_import_api.stream = False
        with patch.object(requests, "post") as mock_post:
            response = Response()
            response.status_code = 200
            response.json = lambda: {"status": "ok"}
            mock_post.return_value = response
            i = 0
            for result in self.source_import_api._get_lines():
                self.assertTrue(result)
                self.assertEqual(result, {"status": "ok"})
                i += 1
            self.assertEqual(1, i)
            mock_post.assert_called_with(
                self.source_import_api._get_url(),
                params=json.dumps(self.source_import_api._get_params()),
                data=json.dumps({"data": "The data"}),
                headers=self.source_import_api._get_headers(),
                timeout=self.source_import_api.timeout,
            )

    def test_data_invisible(self):
        self.assertFalse(self.source_import_api.data_code_invisible)
        self.assertFalse(self.source_import_api.params_code_invisible)
        self.assertFalse(self.source_import_api.stream_invisible)
        self.source_import_api.type_request = "get"
        self.assertTrue(self.source_import_api.data_code_invisible)
        self.assertTrue(self.source_import_api.params_code_invisible)
        self.assertTrue(self.source_import_api.stream_invisible)
