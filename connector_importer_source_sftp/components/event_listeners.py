# Copyright 2019 Camptocamp SA
# @author: Sebastien Alix <sebastien.alix@camptocamp.com>
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import functools

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector_importer.log import logger


class SFTPSourceImportRecordsetEventListener(Component):
    _name = "sftp.source.import.recorset.event.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["import.recordset"]

    @skip_if(lambda self, importer, record: self._skip_move_file(importer, record))
    def on_last_record_import_finished(self, importer, record):
        self._move_file(importer)
        self._report_errors(importer)

    def _skip_move_file(self, importer, record):
        """Check if the file used for the import should be moved.

        :param importer: importer component instance
        :param record: import.record instance (the last one processed)
        """
        if record.env.context.get("_sftp_skip_move_file"):
            return True
        source = importer.recordset.get_source()
        if source._name != "import.source.csv.sftp":
            return True
        return not source.move_file_after_import if source else True

    def _move_file(self, importer):
        """Move file on the SFTP.

        :param importer: importer component instance
        """
        source = importer.recordset.get_source()
        storage = source.storage_id
        sftp_filepath = source._sftp_filepath()
        sftp_destination_path = False

        if self._move_file_to_error(importer):
            sftp_destination_path = source.sftp_path_error
            logger.info(
                "Errors occurred during import, moving the file %s to %s...",
                sftp_filepath,
                sftp_destination_path,
            )
        elif self._move_file_to_success(importer):
            sftp_destination_path = source.sftp_path_success
            logger.info(
                "File imported, moving the file %s to %s...",
                sftp_filepath,
                sftp_destination_path,
            )

        if sftp_destination_path:
            self._add_after_commit_hook(
                storage.move_files, sftp_filepath, sftp_destination_path
            )

    # TODO: make it configurable on the source via code snippet
    # when it should go to errored or success.
    def _move_file_to_error(self, importer):
        """State if file should be moved to error folder."""
        counters = importer.tracker.get_counters()
        return counters["errored"]

    def _move_file_to_success(self, importer):
        """State if file should be moved to success folder."""
        counters = importer.tracker.get_counters()
        return counters["created"] or counters["updated"] or counters["skipped"]

    def _add_after_commit_hook(self, move_func, sftp_filepath, sftp_destination_path):
        """Add hook after commit to move the file when transaction is over."""
        self.env.cr.postcommit.add(
            functools.partial(move_func, [sftp_filepath], sftp_destination_path),
        )

    def _report_errors(self, importer):
        recordset = importer.recordset
        source = recordset.get_source()
        if not source.send_back_error_report or not self._move_file_to_error(importer):
            return
        recordset.generate_report()
        csv_report = recordset.report_file
        if csv_report:
            filepath = source._sftp_filepath("error").replace(".csv", ".report.csv")
            source.storage_id.add(filepath, csv_report, binary=False)
