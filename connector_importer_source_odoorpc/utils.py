# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
logger = logging.getLogger('import.source.odoorpc')
try:
    import odoorpc
except:
    logger.warn('odoorpc lib missing')


class OdooRPCHandler(object):

    required_attrs = (
        'odoo_host', 'odoo_port', 'odoo_protocol',
        'odoo_db', 'odoo_user', 'odoo_pwd',
    )

    def __init__(self, **kw):
        for k, v in kw.items():
            if k in self.required_attrs:
                setattr(self, k, v)

    def connect(self):
        return odoorpc.ODOO(
            self.odoo_host,
            port=self.odoo_port,
            protocol=self.odoo_protocol)

    def connect_and_login(self):
        connection = self.connect()
        connection.login(self.odoo_db, self.odoo_user, self.odoo_pwd)
        return connection
