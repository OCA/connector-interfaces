# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Connector Importer Purchase",
    "summary": "Ease definition of purchases imports using `connector_importer`.",
    "version": "15.0.1.0.0",
    "category": "Tools",
    "website": "https://github.com/OCA/connector-interfaces",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        # oca
        "connector_importer",
        # src
        "purchase",
    ],
    "data": [
        "data/import_type.xml",
    ],
    "demo": [
        "demo/import_backend.xml",
        "demo/import_source.xml",
        "demo/import_recordset.xml",
    ],
    "installable": True,
}
