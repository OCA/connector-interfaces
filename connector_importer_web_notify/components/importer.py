# Copyright 2025 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import logging

from odoo.addons.connector_importer.components.importer import RecordImporter

_logger = logging.getLogger(__name__)


class RecordImporter(RecordImporter):
    def run(self, record, is_last_importer=True, **kw):
        """
        Override the original run method.
        We copy the entire original logic and add the part that collects IDs and
        sends notifications at the end.
        """
        self.record = record
        if not self.record:
            _logger.error("NO RECORD FOUND, maybe deleted? Check your jobs!")
            return

        self._init_importer(self.record.recordset_id)

        processed_record_ids = []

        for line in self._record_lines():
            line = self.prepare_line(line)
            options = self._load_mapper_options()
            odoo_record = None
            try:
                with self.env.cr.savepoint():
                    values = self.mapper.map_record(line).values(**options)
                _logger.debug(values)
            except Exception as err:
                values = {}
                self.tracker.log_error(values, line, odoo_record, message=err)
                if self.must_break_on_error:
                    raise
                continue

            skip_info = self.skip_it(values, line)
            if skip_info:
                self.tracker.log_skipped(values, line, skip_info)
                continue

            try:
                with self.env.cr.savepoint():
                    if self.record_handler.odoo_exists(values, line):
                        odoo_record = self.record_handler.odoo_write(values, line)
                        self.tracker.log_updated(values, line, odoo_record)
                    else:
                        if self.work.options.importer.write_only:
                            self.tracker.log_skipped(
                                values,
                                line,
                                {"message": "Write-only importer, record not found."},
                            )
                            continue
                        odoo_record = self.record_handler.odoo_create(values, line)
                        self.tracker.log_created(values, line, odoo_record)

                    if odoo_record:
                        processed_record_ids.append(odoo_record.id)

            except Exception as err:
                self.tracker.log_error(values, line, odoo_record, message=err)
                if self.must_break_on_error:
                    raise
                continue

        self._do_report()
        counters = self.tracker.get_counters()
        msg = " ".join(
            [
                "CHUNK FINISHED",
                "[created: {created}]",
                "[updated: {updated}]",
                "[skipped: {skipped}]",
                "[errored: {errored}]",
            ]
        ).format(**counters)
        self.tracker._log(msg)

        if processed_record_ids:
            self._send_result_notification(processed_record_ids)

        self.finalize_session(record, is_last_importer=is_last_importer)
        return counters

    def _send_result_notification(self, record_ids):
        model_name = self.model._name
        model_description = self.env["ir.model"]._get(model_name).name or self.env._(
            "Records"
        )

        message = self.env._(
            "%(count)s %(model_name)s have been processed.",
            count=len(record_ids),
            model_name=model_description,
        )

        action = {
            "display_name": "Processed Records",
            "type": "ir.actions.act_window",
            "name": model_description,
            "res_model": model_name,
            "view_mode": "list,form",
            "domain": [("id", "in", record_ids)],
            "target": "current",
            "context": {"params": {"button_name": "Processed Records"}},
        }

        self.env.user.notify_info(
            message=message,
            title="Processed Records",
            sticky=True,
            action=action,
        )
