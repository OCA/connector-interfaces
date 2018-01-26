# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

import requests

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class ImportSourceApi(models.Model):
    _name = "import.source.api"
    _inherit = "import.source"
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
    field_ids = fields.Many2many(
        "ir.model.fields", compute="_compute_field_ids", store=True
    )
    field_id = fields.Many2one("ir.model.fields", domain="[('id', 'in', field_ids)]")
    function_name = fields.Char()
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
        # if self._source_type == "api":
        #     summary_fields = []
        return summary_fields

    def get_config_view_id(self):
        res = super().get_config_view_id()
        if self._source_type == "api":
            return self.env.ref("connector_importer.importer_source_api_view_form").id
        return res

    def _get_eval_context(self, eval_context=None):
        context = {"self": self, "env": self.env} | (eval_context or {})
        return context

    def _get_eval_value(self, eval_variables=None):
        values = {"result": ""} | (eval_variables or {})
        return values

    def _eval_source(self, eval_code=None, eval_variables=None, eval_context=None):
        value = self._get_eval_value(eval_variables)
        context = self._get_eval_context(eval_context)
        if value.get("result", False) is not False:
            safe_eval(eval_code, context, value, mode="exec", nocopy=True)
        else:
            raise ValidationError(
                _("The variable result does not exist, please verify.")
            )
        return value["result"]

    def _get_token(self):
        if self.model_id.model == "res.company":
            eval_code = "result = self.company_id"
        else:
            eval_code = (
                f"result = env['{self.model_id.model}']"
                f".with_company({self.company_id.id})"
                f".search([],limit=1)"
            )
        if self.type_of_token == "model_field" and not self.token:
            eval_code = f"{eval_code}.{self.field_id.name}"
            self.token = self._eval_source(eval_code=eval_code)
        elif self.type_of_token == "model_function" and not self.token:
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
        headers = self._get_headers()
        params = self._get_params()
        data = self._get_data()
        response = requests.request(
            self.type_request,
            self._get_url(),
            headers=headers,
            params=params,
            data=data,
            timeout=15,
        )
        if response.status_code == 200:
            return response.json().get("tickets", [{}])
        else:
            _logger.error(
                f"ERROR SOURCE {self.name}: {response.status_code}: {response.text}"
            )
        return [{}]

    def _get_lines(self):
        return self._process_values()
