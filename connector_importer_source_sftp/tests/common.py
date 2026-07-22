# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.tests.common import (
    TransactionComponentCase,
    TransactionComponentRegistryCase,
)
from odoo.addons.connector_importer.tests.common import TestImporterMixin


class TestSourceCSVSFTPMixin:
    @classmethod
    def _setup_source_records(cls):
        cls.storage_backend = cls.env["storage.backend"].create(
            {
                "name": "SFTP Backend",
                "backend_type": "sftp",
                "sftp_login": "foo",
                "sftp_password": "pass",
                "sftp_server": "localhost",
                "sftp_port": 2222,
                "directory_path": "upload",
            }
        )
        cls.source = cls.env["import.source.csv.sftp"].create(
            {
                "name": "demo_source_sftp_csv",
                "csv_delimiter": ",",
                "csv_encoding": "utf-8",
                "storage_id": cls.storage_backend.id,
                "sftp_filename_pattern": r".*\.csv$",
                "move_file_after_import": False,
                "sftp_path_input": "input",
                "sftp_path_error": "error",
                "sftp_path_success": "success",
            }
        )


class SFTPSourceTransactionComponentCase(
    TransactionComponentCase, TestImporterMixin, TestSourceCSVSFTPMixin
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_records()
        cls._setup_source_records()


class SFTPSourceTransactionComponentRegistryCase(
    TransactionComponentRegistryCase, TestImporterMixin, TestSourceCSVSFTPMixin
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_registry(cls)
        cls._setup_records()
        cls._setup_source_records()

    def setUp(self):
        super().setUp()
        self._setup_components()

    @classmethod
    def tearDownClass(cls):
        cls._teardown_registry(cls)
        super().tearDownClass()

    def _get_component_modules(self):
        return super()._get_component_modules() + ["connector_importer_source_sftp"]
