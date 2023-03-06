# Copyright 2019 Camptocamp SA
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Connector Importer Source SFTP",
    "summary": """Add import source capable of loading files from SFTP.""",
    "version": "15.0.1.0.1",
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
    # Place an upper bound on cryptography version to be compatible with
    # pyopenssl 19 mentioned in Odoo 15's requirements.txt. If we don't do
    # this, installing this module will try to upgrade cryptography to the latest
    # version because the minimum required version in pyopenssl (>=3.1) is greater than
    # version 2.6 (from Odoo's requirement.txt). Since cryptography/pyopenssl don't
    # declare minimum supported versions, this lead to inconsistencies.
    # https://github.com/OCA/server-auth/issues/424
    # https://github.com/OCA/storage/pull/247
    # https://github.com/OCA/connector-interfaces/pull/94
    "external_dependencies": {"python": ["cryptography<37"]},
    "data": ["views/source_csv_sftp.xml", "security/ir.model.access.csv"],
    "demo": ["demo/storage_backend_demo.xml", "demo/import_source_demo.xml"],
}
