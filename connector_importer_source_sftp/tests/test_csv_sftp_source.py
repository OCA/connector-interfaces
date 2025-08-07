# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

import mock

from odoo.tools import mute_logger

from .common import SFTPSourceSavepointComponentCase


class TestSourceCSV(SFTPSourceSavepointComponentCase):

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
    def test_source_get_lines(self):
        source = self.source
        storage = source.storage_id
        # Cannot mock paramiko.SFTPClient here because it failed somehow on CI.
        # Not a big issue since the goal here is to ensure that
        # client = mocked_paramiko.SFTPClient.from_transport()
        mocked_filepaths = [
            storage.directory_path + "/somepath/file.csv",
        ]
        filecontent = self.load_filecontent(
            "connector_importer", "tests/fixtures/csv_source_test1.csv", mode="rb"
        )
        with (
            mock.patch.object(
                type(source.storage_id), "find_files"
            ) as mocked_find_files,
            mock.patch.object(
                type(source.storage_id),
                "get",
            ) as mocked_get_storage,
        ):
            mocked_find_files.return_value = mocked_filepaths
            mocked_get_storage.return_value = base64.b64encode(filecontent)
            source._get_lines()

        self.assertEqual(source.csv_filename, "file.csv")
        self.assertEqual(source.csv_file, base64.b64encode(filecontent))
