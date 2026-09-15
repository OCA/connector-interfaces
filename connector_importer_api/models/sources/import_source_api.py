# Copyright 2025 Binhex <https://www.binhex.cloud>
# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import json
from ast import literal_eval
from contextlib import contextmanager
from itertools import chain

import requests

from odoo import Command, api, fields, models

from ...exceptions.exceptions import InvalidAPIData


class ImportSourceApi(models.Model):
    _name = "import.source.api"
    _inherit = ["import.source", "connector.importer.api.mixin"]
    _description = "API import source"
    _source_type = "api"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    enviroment = fields.Selection(
        selection=[("test", "Test"), ("prod", "Production")],
        default="test",
        required=True,
    )
    enviroment_url = fields.Char(string="Enviroment URL", required=True)
    type_request = fields.Selection(
        string="Request type",
        selection=[("get", "GET"), ("post", "POST")],
        default="get",
        required=True,
    )
    url = fields.Char(string="Endpoint", required=True)
    param_ids = fields.One2many(
        "source.api.value",
        "source_api_params_id",
        string="Params",
    )
    params_code = fields.Json(
        help="This is used for POST API calls in order to allow JSON parameters."
    )
    params_code_invisible = fields.Boolean(
        compute="_compute_params_code_invisible",
    )
    type_authorization = fields.Selection(
        string="Authorization type",
        selection=[
            ("no_auth", "No auth"),
            ("token", "Bearer token"),
            ("basic_auth", "Basic auth"),
        ],
        default="token",
        required=True,
    )
    username = fields.Char()
    password = fields.Char()
    type_of_token = fields.Selection(
        string="Type of token",
        selection=[
            ("manual", "Manual"),
            ("model_field", "Model/Field"),
            ("model_function", "Model/Function"),
        ],
        default="manual",
    )
    token = fields.Char()
    model_id = fields.Many2one("ir.model")
    model_name = fields.Char(related="model_id.model")
    field_ids = fields.Many2many(
        "ir.model.fields", compute="_compute_field_ids", store=True
    )
    field_id = fields.Many2one("ir.model.fields", domain="[('id', 'in', field_ids)]")
    function_name = fields.Char()
    model_domain = fields.Text()
    header_ids = fields.One2many(
        "source.api.value",
        "source_api_header_id",
        string="Headers",
    )
    stream = fields.Boolean(
        help="Check this if your POST endpoint has stream capabilites."
    )
    stream_invisible = fields.Boolean(compute="_compute_stream_invisible")
    timeout = fields.Integer(
        help="This is the request timeout in seconds",
        default=5,
        required=True,
    )

    @api.depends("type_request")
    def _compute_stream_invisible(self):
        for record in self:
            if record.type_request == "get":
                record.stream_invisible = True
            else:
                record.stream_invisible = False

    @api.depends("type_request")
    def _compute_params_code_invisible(self):
        for record in self:
            if record.type_request == "get":
                record.params_code_invisible = True
            else:
                record.params_code_invisible = False

    def _compute_name(self):
        res = super()._compute_name()
        if self._source_type == "api":
            self.name = "SOURCE API"
        return res

    @api.depends("model_id")
    def _compute_field_ids(self):
        for source in self:
            source.field_ids = [
                Command.set(
                    [
                        field.id
                        for field in source.model_id.field_id
                        if field.ttype == "char" and "token" in field.name
                    ]
                )
            ]

    @property
    def _config_summary_fields(self):
        summary_fields = super()._config_summary_fields
        if self._source_type == "api":
            summary_fields = list(
                chain(
                    summary_fields,
                    [
                        "company_id",
                        "enviroment",
                        "type_request",
                        "enviroment_url",
                        "url",
                        "type_authorization",
                    ],
                )
            )
        return summary_fields

    def get_config_view_id(self):
        res = super().get_config_view_id()
        if self._source_type == "api":
            return self.env.ref(
                "connector_importer_api.importer_source_api_view_form"
            ).id
        return res

    def _get_eval_code(self):
        domain = literal_eval(self.model_domain) if self.model_domain else []
        eval_code = (
            f"result = env['{self.model_id.model}']"
            f".with_company({self.company_id.id})"
            f".search({domain},limit=1)"
        )
        return eval_code

    def _get_token(self):
        eval_code = self._get_eval_code()
        if self.type_of_token == "model_field":
            eval_code = f"{eval_code}.{self.field_id.name}"
            self.token = self._eval_source(eval_code=eval_code)
        elif self.type_of_token == "model_function":
            eval_code = f"{eval_code}.{self.function_name}()"
            self.token = self._eval_source(eval_code=eval_code)
        return self.token

    def _get_headers(self):
        token = self._get_token()
        headers = {}
        if token and self.type_authorization == "token":
            headers.update({"Authorization": f"Bearer {token}"})
        if self.type_request == "post" and self.type_authorization == "basic_auth":
            # Basic auth for POST requests are provided in headers
            token = self._get_basic_auth_header()
            headers.update({"Authorization": f"Basic {token}"})
        for header in self.header_ids:
            headers.update({header.name: header.value})
        return headers

    def _get_params(self) -> dict:
        params = {}
        # Json parameters have sense only in POST requests
        if self.type_request == "post" and self.params_code:
            params = self.params_code
        for param in self.param_ids:
            params.update({param.name: param.value})
        return params

    def _get_data(self):
        return {}

    def _get_url(self):
        return f"{self.enviroment_url}{self.url}"

    def _get_basic_auth_header(self):
        """
        Encode Basic Auth Header for POST requests
        """
        credentials = f"{self.username}:{self.password}"
        auth = (
            base64.b64encode(credentials.encode("utf-8"))
            .decode("utf-8")
            .replace("\n", "")
        )
        return auth

    def _process_values(self):
        """
        This method can be overridden in the extending
        module to retrieve and process data as needed.

        Consider the following methods:
            _get_headers: Retrieves the configured headers.
            _get_params: Retrieves the configured parameters.

        The method must return a list of dictionaries or an empty list.

        """

        data = self._get_data()
        if data and not isinstance(data, dict):
            raise InvalidAPIData(
                self.env,
                self.env._(
                    "Import '%(importer_name)s' cannot process data values",
                    importer_name=self.name,
                ),
            )
        data = json.dumps(data)
        params = self._get_params()
        if params and not isinstance(params, dict):
            raise InvalidAPIData(
                self.env,
                self.env._(
                    "Import '%(importer_name)s' cannot process params values",
                    importer_name=self.name,
                ),
            )
        params = json.dumps(params)
        headers = self._get_headers()
        url = self._get_url()

        if self.type_request == "post":
            with self._get_post_result(
                url, data=data, params=params, headers=headers, stream=self.stream
            ) as results:
                yield results
        else:
            return requests.get(
                url, data=data, params=params, headers=headers, timeout=self.timeout
            )

    @contextmanager
    def _get_post_result(self, url, data, params, headers, stream=False):
        if stream:
            # Iterate on response lines
            with requests.post(
                url,
                data=data,
                params=params,
                headers=headers,
                stream=self.stream,
                timeout=self.timeout,
            ) as results:
                for result in results.iter_lines():
                    result_data = json.loads(result)
                    yield result_data
        else:
            response = requests.post(
                url, data=data, params=params, headers=headers, timeout=self.timeout
            )
            result_data = response.json()
            yield result_data

    def _get_lines(self):
        result = self._process_values()
        return result
