# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..utils import OdooRPCHandler
from odoo import models, fields, api, exceptions, _


class OdooRPCConfig(models.Model):
    _name = 'import.odoorpc.config'

    odoo_host = fields.Char(required=True)
    odoo_port = fields.Char(required=True, default='8069')
    odoo_protocol = fields.Char(required=True, default='jsonrpc+ssl')
    odoo_db = fields.Char(required=True)
    odoo_user = fields.Char(required=True)
    odoo_pwd = fields.Char(required=True)

    def _rpc_connect_data(self):
        data = self.read()[0]
        del data['id']
        data['odoo_port'] = int(data['odoo_port'])
        return data

    @api.multi
    def action_test_connection(self):
        self.ensure_one()
        data = self._rpc_connect_data()
        handler = OdooRPCHandler(**data)
        conn = handler.connect_and_login()
        if conn:
            raise exceptions.UserError(_('Connection successful'))
