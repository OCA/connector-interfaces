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
        cls.source = cls.env.ref(
            "connector_importer_source_sftp.demo_import_source_csv_sftp"
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
        cls._setup_records()
        cls._setup_source_records()

    def setUp(self):
        super().setUp()
        self._setup_registry(self)
        self._setup_components()

    def _get_component_modules(self):
        return super()._get_component_modules() + ["connector_importer_source_sftp"]
