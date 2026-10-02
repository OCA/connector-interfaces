# Copyright 2026 ACSONE SA/NV <https://acsone.eu>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.api import Environment
from odoo.exceptions import ValidationError


class InvalidAPIData(ValidationError):
    def __init__(self, env: Environment, message):
        self.env = env
        msg = self.env._("Invalid Importer API Data:\n")
        msg += message
        super().__init__(msg)
