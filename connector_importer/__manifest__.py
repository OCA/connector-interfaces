# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Connector Importer",
    "summary": """This module takes care of import sessions.""",
    "version": "15.0.1.3.0",
    "depends": ["connector", "queue_job"],
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Connector",
    "website": "https://github.com/OCA/connector-interfaces",
    "maintainers": ["simahawk"],
    "data": [
        "data/ir_cron.xml",
        "data/queue_job_function_data.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/backend_views.xml",
        "views/recordset_views.xml",
        "views/import_type_views.xml",
        "views/source_views.xml",
        "views/report_template.xml",
        "views/docs_template.xml",
        "views/source_config_template.xml",
        "menuitems.xml",
    ],
    "external_dependencies": {"python": ["chardet", "pytz", "pyyaml"]},
}
