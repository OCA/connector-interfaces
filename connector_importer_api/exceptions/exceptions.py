# Copyright 2026 ACSONE SA/NV <https://acsone.eu>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from requests import Response

from odoo.api import Environment
from odoo.exceptions import UserError, ValidationError


class InvalidAPIData(ValidationError):
    def __init__(self, env: Environment, message):
        self.env = env
        msg = self.env._("Invalid Importer API Data:\n")
        msg += message
        super().__init__(msg)


class APIRequestError(UserError):
    def __init__(self, env: Environment, response: Response, message=False):
        self.env = env
        msg = self.env._(
            "API Request Error: (%(error_code)s) - %(error_name)s \n",
            error_code=response.status_code,
            error_name=response.reason,
        )
        if message:
            msg += message
        super().__init__(msg)
