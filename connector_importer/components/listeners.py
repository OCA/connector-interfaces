# Copyright 2023 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from functools import partial

from odoo.addons.component.core import Component


class ImportRecordsetEventListener(Component):
    _name = "recordset.event.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["import.recordset"]

    def on_last_record_import_finished(self, importer, record):
        if self._must_run_server_action(importer, record, "last_importer_done"):
            self._run_server_actions(importer, record)

    def on_record_import_finished(self, importer, record):
        if self._must_run_server_action(importer, record, "each_importer_done"):
            self._run_server_actions(importer, record)

    def _must_run_server_action(self, importer, record, trigger):
        recordset = record.recordset_id
        return bool(
            recordset.server_action_ids
            and recordset.server_action_trigger_on == trigger
            and self._has_records_to_process(importer)
        )

    def _has_records_to_process(self, importer):
        counters = importer.tracker.get_counters()
        return counters["created"] or counters["updated"]

    def _run_server_actions(self, importer, record):
        """Execute one or more server actions tied to the recordset."""
        recordset = record.recordset_id
        actions = recordset.server_action_ids
        report_by_model = recordset.get_report_by_model()
        # execute actions by importer order
        for model, report in report_by_model.items():
            action = actions.filtered(lambda x: x.model_id == model)
            if not action:
                continue
            record_ids = sorted(set(report["created"] + report["updated"]))
            if not record_ids:
                continue
            self._add_after_commit_hook(recordset.id, action.id, record_ids)
        generic_action = actions.filtered(
            lambda x: x.model_id.model == "import.recordset"
        )
        if generic_action:
            self._add_after_commit_hook(recordset.id, generic_action.id, recordset.ids)

    def _run_server_action(self, recordset_id, action_id, record_ids):
        action = self.env["ir.actions.server"].browse(action_id)
        action = action.with_context(
            **self._run_server_action_ctx(recordset_id, action_id, record_ids)
        )
        return action.run()

    def _run_server_action_ctx(self, recordset_id, action_id, record_ids):
        action = self.env["ir.actions.server"].browse(action_id)
        action_ctx = dict(
            active_model=action.model_id.model, import_recordset_id=recordset_id
        )
        if len(record_ids) > 1:
            action_ctx["active_ids"] = record_ids
        else:
            action_ctx["active_id"] = record_ids[0]
        return action_ctx

    def _add_after_commit_hook(self, recordset_id, action_id, record_ids):
        self.env.cr.postcommit.add(
            partial(
                self._run_server_action_post_commit, recordset_id, action_id, record_ids
            ),
        )

    def _run_server_action_post_commit(self, recordset_id, action_id, record_ids):
        self._run_server_action(recordset_id, action_id, record_ids)
        self.env.cr.commit()  # pylint: disable=invalid-commit
