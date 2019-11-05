# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Connector Importer Demo",
    "summary": """Demo module for Connector Importer.""",
    "version": "13.0.1.0.0",
    "depends": ["connector_importer"],
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Connector",
    "website": "https://github.com/OCA/connector-interfaces",
    "post_init_hook": "post_init_hook",
    "data": [
        "data/import_backend.xml",
        "data/import_type.xml",
        "data/import_source.xml",
        "data/import_recordset.xml",
    ],
}
