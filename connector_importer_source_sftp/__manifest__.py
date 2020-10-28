# Copyright 2019 Camptocamp SA
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Connector Importer Source SFTP",
    "summary": """Add import source capable of loading files from SFTP.""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp,ACSONE,Odoo Community Association (OCA)",
    "maintainers": ["simahawk", "sebalix"],
    "website": "https://github.com/OCA/connector-interfaces",
    # fmt: off
    "depends": [
        "connector_importer",
        "component_event",
        "storage_backend_sftp",
    ],
    # fmt: on
    "data": ["views/source_csv_sftp.xml", "security/ir.model.access.csv"],
    "demo": ["demo/storage_backend_demo.xml", "demo/import_source_demo.xml"],
}
