# Copyright 2026 ACSONE SA/NV <https://acsone.eu>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from io import StringIO
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
            response.json = lambda: {"status": "ok"}
            response.raw = StringIO('{"status": "ok"}')
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
            response.raw = StringIO('{"status": "ok"}')
            mock_post.return_value = response
            results = self.source_import_api._get_lines()
            for result in results:
                self.assertEqual("ok", result.get("status"))
