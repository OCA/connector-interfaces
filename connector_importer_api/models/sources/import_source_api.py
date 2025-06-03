# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from ast import literal_eval
from itertools import chain

from odoo import Command, api, fields, models


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
        selection=[("get", "GET")],
        default="get",
        required=True,
    )
    url = fields.Char(string="Endpoint", required=True)
    param_ids = fields.One2many(
        "source.api.value",
        "source_api_params_id",
        string="Params",
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
        if token:
            headers.update({"Authorization": f"Bearer {token}"})
        for header in self.header_ids:
            headers.update({header.name: header.value})
        return headers

    def _get_params(self):
        params = {}
        for param in self.param_ids:
            params.update({param.name: param.value})
        return params

    def _get_data(self):
        return {}

    def _get_url(self):
        return f"{self.enviroment_url}{self.url}"

    def _process_values(self):
        """
        This method can be overridden in the extending
        module to retrieve and process data as needed.

        Consider the following methods:
            _get_headers: Retrieves the configured headers.
            _get_params: Retrieves the configured parameters.

        The method must return a list of dictionaries or an empty list.

        """
        return []

    def _get_lines(self):
        return self._process_values()
