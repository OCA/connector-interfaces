# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.component.core import Component


class ChunkReport(dict):
    """A smarter dict for chunk reports."""

    chunk_report_keys = ("created", "updated", "errored", "skipped")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k in self.chunk_report_keys:
            self[k] = []

    def track_error(self, item):
        self["errored"].append(item)

    def track_skipped(self, item):
        self["skipped"].append(item)

    def track_updated(self, item):
        self["updated"].append(item)

    def track_created(self, item):
        self["created"].append(item)

    def counters(self):
        res = {}
        for k, v in self.items():
            res[k] = len(v)
        return res


class Tracker(Component):
    """Track what happens during importer jobs."""

    _name = "importer.tracking.handler"
    _inherit = "importer.base.component"
    _usage = "tracking.handler"

    model_name = ""
    logger_name = ""
    log_prefix = ""
    _chunk_report_klass = ChunkReport

    def _init_handler(self, model_name="", logger_name="", log_prefix=""):
        self.model_name = model_name
        self.logger_name = logger_name
        self.log_prefix = log_prefix

    _logger = None
    _chunk_report = None

    @property
    def logger(self):
        if not self._logger:
            self._logger = logging.getLogger(self.logger_name)
        return self._logger

    @property
    def chunk_report(self):
        if not self._chunk_report:
            self._chunk_report = self._chunk_report_klass()
        return self._chunk_report

    def chunk_report_item(self, line, odoo_record=None, message="", values=None):
        return {
            "line_nr": line["_line_nr"],
            "message": message,
            "model": self.model_name,
            "odoo_record": odoo_record.id if odoo_record else None,
        }

    def _log(self, msg, line=None, level="info"):
        handler = getattr(self.logger, level)
        msg = "{prefix}{line}[model: {model}] {msg}".format(
            prefix=self.log_prefix,
            line="[line: {}]".format(line["_line_nr"]) if line else "",
            model=self.model_name,
            msg=msg,
        )
        handler(msg)

    def log_updated(self, values, line, odoo_record=None, message=""):
        if odoo_record:
            self._log("UPDATED [id: {}]".format(odoo_record.id), line=line)
        self.chunk_report.track_updated(
            self.chunk_report_item(
                line, odoo_record=odoo_record, message=message, values=values
            )
        )

    def log_error(self, values, line, odoo_record=None, message=""):
        if isinstance(message, Exception):
            message = str(message)
        self._log(message, line=line, level="error")
        self.chunk_report.track_error(
            self.chunk_report_item(
                line, odoo_record=odoo_record, message=message, values=values
            )
        )

    def log_created(self, values, line, odoo_record=None, message=""):
        if odoo_record:
            self._log("CREATED [id: {}]".format(odoo_record.id), line=line)
        self.chunk_report.track_created(
            self.chunk_report_item(
                line, odoo_record=odoo_record, message=message, values=values
            )
        )

    def log_skipped(self, values, line, skip_info):
        # `skip_it` could contain a msg
        self._log("SKIPPED " + skip_info.get("message"), line=line, level="warning")

        item = self.chunk_report_item(line, values=values)
        item.update(skip_info)
        self.chunk_report.track_skipped(item)

    def get_report(self, previous=None):
        previous = previous or {}
        # init a new report
        report = self._chunk_report_klass()
        # merge previous and current
        for k, _v in report.items():
            prev = previous.get(self.model_name, {}).get(k, [])
            report[k] = prev + self.chunk_report[k]
        return report

    def get_counters(self):
        return self.chunk_report.counters()
