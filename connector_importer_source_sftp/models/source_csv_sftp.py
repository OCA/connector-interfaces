# Copyright 2019 Camptocamp SA (<http://camptocamp.com>)
# @author: Sebastien Alix <sebastien.alix@camptocamp.com>
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging
import os

from odoo import fields, models

_logger = logging.getLogger(__name__)


# TODO: in the future, split this to a generic mixin not tied to CSV.
class ImportSourceCSVSFTP(models.Model):
    """Import source for CSV files on SFTP."""

    _name = "import.source.csv.sftp"
    _inherit = [
        "import.source.csv",
    ]
    _description = "CSV import source through SFTP"
    _source_type = "csv_sftp"

    # Overrided to get a store field for env purpose
    name = fields.Char(compute=False)
    storage_id = fields.Many2one(
        string="Storage backend",
        comodel_name="storage.backend",
        required=True,
        ondelete="restrict",
        domain=[("backend_type", "=", "sftp")],
    )
    sftp_path_input = fields.Char(
        string="SFTP Folder path - Input",
        required=True,
        default="pending",
        help=("Where to find CSV files to import. Eg: `/mnt/csv/res_partner/pending/`"),
    )
    sftp_path_error = fields.Char(
        string="SFTP Folder path - Error",
        required=True,
        default="error",
        help=(
            "Where to move CSV files if errors occurred "
            "when `Move file after import` is enabled. "
            "Eg: `/mnt/csv/res_partner/error/`"
        ),
    )
    sftp_path_success = fields.Char(
        string="SFTP Folder path - Success",
        required=True,
        default="done",
        help=(
            "Where to move CSV files if no errors occurred "
            "when `Move file after import` is enabled. "
            "Eg: `/mnt/csv/res_partner/done/`"
        ),
    )
    sftp_filename_pattern = fields.Char(
        string="SFTP Filename pattern",
        required=True,
        default=r".*\.csv$",
        help="Regex pattern to match CSV file names.",
    )
    move_file_after_import = fields.Boolean(
        help="If enabled, the file processed will be moved to success/error folders "
        "depending on the result of the import"
    )
    # TODO: this should probably stay at recordset level
    send_back_error_report = fields.Boolean(
        help="If enabled, the CSV report will be generated and put in the error folder"
    )

    @property
    def _config_summary_fields(self):
        _fields = super()._config_summary_fields
        _fields.extend(
            [
                "storage_id",
                "sftp_path_input",
                "sftp_filename_pattern",
                "move_file_after_import",
                "send_back_error_report",
            ]
        )
        if self.move_file_after_import:
            _fields.extend(["sftp_path_error", "sftp_path_success"])
        return _fields

    def _get_lines(self):
        """Get lines from file on sftp server.

        Gets file from SFTP server and passes it to csv_file field to keep
        standard csv source machinery. Overwrites it on every run, so the file
        pattern should be defined in sftp_filename_pattern field.
        """
        self.csv_filename, self.csv_file = self._sftp_get_file()
        if self.csv_filename:
            if self.csv_file:
                return super()._get_lines()
            else:
                _logger.info(
                    "Empty or unreadable file on SFTP server: '%s'", self.csv_filename
                )
        else:
            _logger.info("No matching file found on SFTP server")
        return []

    def _sftp_get_file(self):
        """Try to read the first file matching the pattern.

        Return a tuple (filename, filedata).
        """
        filepaths = self._sftp_find_files()
        filename = None
        filedata = None
        if filepaths:
            filedata = self._sftp_read_file(filepaths[0])
            filename = os.path.basename(filepaths[0])
        return filename, filedata

    def _sftp_find_files(self):
        return self.storage_id.find_files(
            self.sftp_filename_pattern, relative_path=self.sftp_path_input
        )

    def _sftp_read_file(self, filepath):
        return self.storage_id.get(filepath, binary=False)

    def _sftp_filepath(self, path_suffix="input"):
        base_path = (self["sftp_path_" + path_suffix] or "").rstrip("/ ")
        return os.path.join(base_path, self.csv_filename.strip("/ "))
