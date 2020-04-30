# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import base64
import csv
import io
import time

from odoo import api, models

from ..utils.import_utils import get_encoding


class ReporterMixin(models.AbstractModel):
    """Base mixin for reporters.

    A reporter can be used to produce a file with a summary of the import
    that the user can generate and download on each recordset.

    The summary can be anything you like: you are in total control of it.
    See the CSV example for a real case.
    """

    _name = "reporter.mixin"
    _description = "Base mixin for reporters"

    report_extension = ".txt"

    @api.model
    def report_get(self, recordset, **options):
        """Create and return a report for given recordset."""
        with io.StringIO() as fileout:
            self.report_do(recordset, fileout, **options)
            self.report_finalize(recordset, fileout, **options)
            metadata = self.report_get_metadata(recordset, **options)
            return metadata, fileout.getvalue()

    def report_do(self, recordset, fileout, **options):
        """Override me to generate the report."""
        raise NotImplementedError()

    def report_finalize(self, recordset, fileout, **options):
        """Apply late updates to report."""

    def report_get_metadata(self, recordset, **options):
        """Retrieve report file's metadata."""
        fname = str(time.time())
        ext = self.report_extension
        return {"filename": fname, "ext": ext, "complete_filename": fname + ext}


class CSVReporter(models.AbstractModel):
    """Produce a CSV report.

    Very often is not easy to let the customer know what went wrong.
    Here a CSV report is generated based on the initial CSV
    provided by the customer/user.

    Basically we:

    * compute the stats of errored and skipped _get_lines
    * clone the original CSV file
    * add new columns at the end

    The new columns number is controlled by the flag `report_group_by_status`:

    * True: 2 new columns per each model imported. For instance:
        * [R] res.partner skipped
        * [R] res.partner errored
        * [R] res.partner.category skipped
        * [R] res.partner.category errored
    * False: errors are grouped by state in 2 columns:
        * [R] skipped
        * [R] errored

    In this way the end user can check side by side which lines went wrong.
    """

    _name = "reporter.csv"
    _description = "Reporter producing a CSV report"
    _inherit = "reporter.mixin"

    report_extension = ".csv"
    # columns to track/add
    report_keys = ["skipped", "errored"]
    # Flag to determine if status report must be grouped by status.
    # If `True` report result will be merged by status (errored, skipped, ...)
    report_group_by_status = True

    def report_get_writer(self, fileout, columns, delimiter=";", quotechar='"'):
        writer = csv.DictWriter(
            fileout,
            columns,
            delimiter=delimiter,
            quoting=csv.QUOTE_NONNUMERIC,
            quotechar=quotechar,
        )
        writer.writeheader()
        return writer

    def report_add_line(self, writer, item):
        writer.writerow(item)

    def report_get_columns(
        self, recordset, orig_content, extra_keys=None, delimiter=";", quotechar='"'
    ):
        """Retrieve columns by recordset.

        :param recordset: instance of recordset.
        :param orig_content: original csv content list of line.
        :param extra_keys: report-related extra columns.
        """
        extra_keys = extra_keys or []
        # read only the 1st line of the original file
        if orig_content:
            reader = csv.reader(
                orig_content[:1], delimiter=delimiter, quotechar=quotechar
            )
            columns = next(reader)
            return columns + extra_keys
        return extra_keys

    def report_do(self, recordset, fileout, **options):
        """Produce report."""
        json_report = recordset.get_report()
        report_keys = options.get("report_keys", self.report_keys)
        group_by_status = options.get("group_by_status", self.report_group_by_status)

        model_keys = [x for x in json_report.keys() if not x.startswith("_")]

        extra_keys = [self._report_make_key(x) for x in report_keys]
        if not group_by_status:
            # we produce one column per-model per-status
            for model in model_keys:
                for key in report_keys:
                    extra_keys.append(self._report_make_key(key, model=model))

        source = recordset.get_source()
        csv_file_bin = base64.b64decode(source.csv_file)
        # Try to guess the encoding of the file supplied
        csv_file_encoding = get_encoding(csv_file_bin).get("encoding", "utf-8")
        orig_content = csv_file_bin.decode(csv_file_encoding).splitlines()
        delimiter = source.csv_delimiter
        quotechar = source.csv_quotechar

        columns = self.report_get_columns(
            recordset,
            orig_content,
            extra_keys=extra_keys,
            delimiter=delimiter,
            quotechar=quotechar,
        )

        writer = self.report_get_writer(
            fileout, columns, delimiter=delimiter, quotechar=quotechar
        )

        reader = csv.DictReader(orig_content, delimiter=delimiter, quotechar=quotechar)

        self._report_do(
            json_report=json_report,
            reader=reader,
            writer=writer,
            model_keys=model_keys,
            report_keys=report_keys,
            group_by_status=group_by_status,
        )

    def _report_do(
        self,
        json_report=None,
        reader=None,
        writer=None,
        model_keys=None,
        report_keys=None,
        group_by_status=True,
    ):

        line_handler = self._report_line_by_model_and_status
        if group_by_status:
            line_handler = self._report_line_by_status

        grouped = self._report_group_by_line(json_report, model_keys, report_keys)

        for line in reader:
            line_handler(line, reader.line_num, grouped, model_keys)
            self.report_add_line(writer, line)

    def _report_make_key(self, key, model=""):
        if model:
            return "[R] {}: {}".format(model, key)
        return "[R] {}".format(key)

    def _report_group_by_line(self, json_report, model_keys, report_keys):
        """Group report items by line number.

        Return something like:

        {
            'errored': {},
            'skipped': {
                2: [
                    {
                        u'line_nr': 2,
                        u'message': u'MISSING REQUIRED KEY=foo',
                        u'model': u'product.supplierinfo',
                        u'odoo_record': None
                    },
                    {
                        u'line_nr': 2,
                        u'message': u'MISSING REQUIRED KEY=bla',
                        u'model': u'product.product',
                        u'odoo_record': None
                    },
                ],
                3: [
                    {
                        u'line_nr': 3,
                        u'message': u'MISSING REQUIRED KEY=foo',
                        u'model': u'product.template',
                        u'odoo_record': None
                    },
                    {
                        u'line_nr': 3,
                        u'message': u'ALREADY_EXISTS code=XXXX',
                        u'model': u'product.product',
                        u'odoo_record': None
                    },
                ],
        }
        """
        by_line = {}
        for model in model_keys:
            # list of messages
            by_model = json_report.get(model, {})
            for key in report_keys:
                by_line.setdefault(key, {})
                for item in by_model.get(key, []):
                    by_line[key].setdefault(item["line_nr"], []).append(item)
        return by_line

    def _report_line_by_model_and_status(self, line, line_num, grouped, model_keys):
        """Get one column per each pair model-status."""
        for model in model_keys:
            for status, lines in grouped.items():
                # get info on current line if any
                line_info = lines.get(line_num, {})
                # add the extra report column anyway
                line[self._report_make_key(model, status)] = line_info.get("message")

    def _report_line_by_status(self, line, line_num, grouped, model_keys):
        """Get one column per each status containing all modelss messages."""
        for status, by_line in grouped.items():
            line_info = by_line.get(line_num, [])
            line[self._report_make_key(status)] = "\n".join(
                ["{model}: {message}".format(**item) for item in line_info]
            )
