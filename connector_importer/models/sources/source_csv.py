# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from odoo import api, fields, models

from ...utils.import_utils import CSVReader, guess_csv_metadata


class CSVSource(models.Model):
    _name = "import.source.csv"
    _inherit = "import.source"
    _description = "CSV import source"
    _source_type = "csv"
    _reporter_model = "reporter.csv"

    csv_file = fields.Binary("CSV file")
    # use these to load file from an FS path
    csv_filename = fields.Char("CSV filename")
    csv_filesize = fields.Char(
        string="CSV filesize", compute="_compute_csv_filesize", readonly=True
    )
    # This is for scheduled import via FS path (FTP, sFTP, etc)
    csv_path = fields.Char("CSV path")
    csv_delimiter = fields.Char(string="CSV delimiter", default=";")
    csv_quotechar = fields.Char(string="CSV quotechar", default='"')
    csv_encoding = fields.Char(string="CSV Encoding")
    csv_rows_from_to = fields.Char(
        string="CSV use only a slice of the available lines. "
        "Format: $from:$to. "
        "NOTE: recommended only for debug/test purpose.",
    )
    # Handy fields to get a downloadable example file
    example_file_ext_id = fields.Char(
        help=(
            "You can define example file by creating attachments "
            "with an external ID matching the 'import.source.csv' record "
            "external ID:\n"
            "\t${import.source.csv.ExtID}_example_file\n\n"
            "You can also specify your own external ID by filling this field."
        )
    )
    example_file_url = fields.Char(
        string="Download example file", compute="_compute_example_file_url"
    )

    _csv_reader_klass = CSVReader

    @property
    def _config_summary_fields(self):
        _fields = super()._config_summary_fields
        return _fields + [
            "csv_filename",
            "csv_filesize",
            "csv_delimiter",
            "csv_quotechar",
            "csv_encoding",
        ]

    def _binary_csv_content(self):
        return base64.b64decode(self.csv_file)

    @api.onchange("csv_file")
    def _onchange_csv_file(self):
        if self.csv_file:
            # auto-guess CSV details
            meta = guess_csv_metadata(self._binary_csv_content())
            if meta:
                self.csv_delimiter = meta["delimiter"]
                self.csv_quotechar = meta["quotechar"]

    @api.depends("csv_file")
    def _compute_csv_filesize(self):
        for item in self:
            item.csv_filesize = False
            if item.csv_file:
                # in v11 binary fields now can return the size of the file
                item.csv_filesize = self.with_context(bin_size=True).csv_file

    def _get_lines(self):
        # read CSV
        reader_args = {
            "delimiter": self.csv_delimiter,
            "encoding": self.csv_encoding,
            "rows_from_to": self.csv_rows_from_to,
        }
        if self.csv_path:
            # TODO: join w/ filename
            reader_args["filepath"] = self.csv_path
        else:
            reader_args["filedata"] = base64.decodebytes(self.csv_file)

        reader = self._csv_reader_klass(**reader_args)
        return reader.read_lines()

    def _get_example_attachment(self):
        self.ensure_one()
        xmlid = self.example_file_ext_id
        if not xmlid:
            source_xmlid = self.get_external_id()[self.id]
            if not source_xmlid:
                return
            xmlid = "{}_example_file".format(source_xmlid)
        return self.env.ref(xmlid, raise_if_not_found=0)

    @api.depends("example_file_ext_id")
    def _compute_example_file_url(self):
        for source in self:
            source.example_file_url = False
            att = source._get_example_attachment()
            if att:
                source.example_file_url = "/web/content/{}/{}".format(att.id, att.name)
