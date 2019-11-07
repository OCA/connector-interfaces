# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64

from odoo import SUPERUSER_ID, api
from odoo.modules.module import get_module_resource


def post_init_hook(cr, _):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        csv_path = get_module_resource(
            "connector_importer_demo", "example", "res.partner.csv"
        )
        with open(csv_path, "rb") as file_:
            data = file_.read()
            source_csv = env.ref("connector_importer_demo.import_source_csv_partner")
            data_b64 = base64.b64encode(data)
            source_csv.csv_file = data_b64
