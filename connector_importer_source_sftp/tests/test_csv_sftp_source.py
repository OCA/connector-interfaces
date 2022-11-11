# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import io

import mock

from odoo.tools import mute_logger

from odoo.addons.storage_backend_sftp.tests.test_sftp import PARAMIKO_PATH

from .common import SFTPSourceTransactionComponentCase


class TestSourceCSV(SFTPSourceTransactionComponentCase):

    extra_fields = [
        "chunk_size",
        "csv_filesize",
        "csv_filename",
        "csv_delimiter",
        "csv_quotechar",
        "csv_encoding",
        "storage_id",
        "sftp_path_input",
        "sftp_filename_pattern",
        "move_file_after_import",
        "sftp_path_error",
        "sftp_path_success",
        "send_back_error_report",
    ]

    @mute_logger("[importer]")
    def test_source_basic(self):
        source = self.source
        self.assertEqual(source.name, "demo_source_sftp_csv")
        # move file not enabled, less fields
        self.assertItemsEqual(
            source._config_summary_fields,
            [
                x
                for x in self.extra_fields
                if x not in ("sftp_path_error", "sftp_path_success")
            ],
        )
        self.assertEqual(source.csv_delimiter, ",")
        self.assertEqual(source.csv_quotechar, '"')
        source.move_file_after_import = True
        self.assertItemsEqual(source._config_summary_fields, self.extra_fields)

    @mute_logger("[importer]")
    @mock.patch(PARAMIKO_PATH)
    def test_source_get_lines(self, mocked_paramiko):
        source = self.source
        storage = source.storage_id
        client = mocked_paramiko.SFTPClient.from_transport()
        mocked_filepaths = [
            storage.directory_path + "/somepath/file.txt",
            storage.directory_path + "/somepath/file.csv",
        ]
        client.listdir.return_value = mocked_filepaths
        filecontent = self.load_filecontent(
            "connector_importer", "tests/fixtures/csv_source_test1.csv", mode="rb"
        )
        with io.BytesIO(filecontent) as file_obj:
            client.open.return_value = file_obj
            source._get_lines()

        self.assertEqual(source.csv_filename, "file.csv")
        self.assertEqual(source.csv_file, base64.b64encode(filecontent))
