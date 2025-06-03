# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Connector Importer API",
    "summary": """This module handles import sessions via API.""",
    "version": "17.0.1.0.0",
    "depends": ["connector_importer"],
    "author": "Binhex, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Connector",
    "website": "https://github.com/OCA/connector-interfaces",
    "data": [
        "security/ir.model.access.csv",
        "views/source_api_value_views.xml",
        "views/source_api_views.xml",
        "views/connector_importer_api_menus.xml",
    ],
}
