# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import os
from collections import OrderedDict

from odoo import api, fields, models

from odoo.addons.base_sparse_field.models.fields import Serialized
from odoo.addons.queue_job.job import DONE, STATES

from ..log import logger
from ..utils.misc import get_importer_for_config


class ImportRecordset(models.Model):
    """Set of records, together with their configuration.

    A recordset can be considered as an "import session".
    Here you declare:

    * what you want to import (via "Import type")
    * where you get records from (via "Source" configuration)

    A recordset is also responsible to hold and display some meaningful
    information about imports:

    * required fields, translatable fields, defaults
    * import stats (created|updated|skipped|errored counters, latest run)
    * fully customizable HTML report to provide more details
    * downloadable report file (via reporters)
    * global states of running jobs

    When you run the import of a recordset this is what it does:

    * ask the source to provide all the records (chunked)
    * create an import record for each chunk
    * schedule the import job for each import record
    """

    _name = "import.recordset"
    _inherit = [
        "import.source.consumer.mixin",
        "job.related.mixin",
    ]
    _description = "Import recordset"
    _order = "sequence ASC, create_date DESC"
    _backend_type = "import_backend"

    backend_id = fields.Many2one("import.backend", string="Import Backend")
    sequence = fields.Integer(help="Sequence for the handle.", default=10)
    import_type_id = fields.Many2one(
        string="Import type", comodel_name="import.type", required=True
    )
    override_existing = fields.Boolean(
        string="Override existing items",
        help="Enable to update existing items w/ new values. "
        "If disabled, matching records will be skipped.",
        default=True,
    )
    name = fields.Char(compute="_compute_name")
    create_date = fields.Datetime()
    record_ids = fields.One2many("import.record", "recordset_id", string="Records")
    # store info about imports report
    report_data = Serialized()
    shared_data = Serialized()
    report_html = fields.Html("Report summary", compute="_compute_report_html")
    full_report_url = fields.Char(compute="_compute_full_report_url")
    jobs_global_state = fields.Selection(
        selection=[("no_job", "No job")] + STATES,
        default="no_job",
        compute="_compute_jobs_global_state",
        help=(
            "Tells you if a job is running for this recordset. "
            "If any of the sub jobs is not DONE or FAILED "
            "we assume the global state is PENDING."
        ),
    )
    report_file = fields.Binary()
    report_filename = fields.Char()
    docs_html = fields.Html(string="Docs", compute="_compute_docs_html")
    notes = fields.Html(help="Useful info for your users")

    def _compute_name(self):
        for item in self:
            item.name = f"#{item.id}"

    def get_records(self):
        """Retrieve importable records and keep ordering."""
        return self.env["import.record"].search([("recordset_id", "=", self.id)])

    def _set_serialized(self, fname, values, reset=False):
        """Update serialized data."""
        _values = {}
        if not reset:
            _values = self[fname]
        _values.update(values)
        self[fname] = _values
        # Without invalidating cache we will have a bug because of Serialized
        # field in odoo. It uses json.loads on convert_to_cache, which leads
        # to all of our int dict keys converted to strings. Except for the
        # first value get, where we get not from cache yet.
        # SO if you plan on using integers as your dict keys for a serialized
        # field beware that they will be converted to strings.
        # In order to streamline this I invalidate cache right away so the
        # values are converted right away
        # TL/DR integer dict keys will always be converted to strings, beware
        self.invalidate_cache((fname,))

    def set_report(self, values, reset=False):
        """Update import report values."""
        self.ensure_one()
        self._set_serialized("report_data", values, reset=reset)

    def get_report(self):
        self.ensure_one()
        return self.report_data or {}

    def set_shared(self, values, reset=False):
        """Update import report values."""
        self.ensure_one()
        self._set_serialized("shared_data", values, reset=reset)

    def get_shared(self):
        self.ensure_one()
        return self.shared_data or {}

    def _prepare_for_import_session(self, start=True):
        """Wipe all session related data."""
        report_data = {}
        if start:
            report_data["_last_start"] = fields.Datetime.to_string(
                fields.Datetime.now()
            )
        values = {
            "record_ids": [(5, 0, 0)],
            "report_data": report_data,
            "shared_data": {},
        }
        self.write(values)
        self.invalidate_cache(tuple(values.keys()))

    def _get_report_html_data(self):
        """Prepare data for HTML report.

        :return dict: containing data for HTML report.

        Keys:
            ``recordset``: current recordset
            ``last_start``: last time import ran
            ``report_by_model``: report data grouped by model. Like:
                data['report_by_model'] = {
                    ir.model(res.parner): {
                        'errored': 1,
                        'skipped': 4,
                        'created': 10,
                        'updated': 8,
                    }
                }
        """
        report = self.get_report()
        data = {
            "recordset": self,
            "last_start": report.pop("_last_start"),
            "report_by_model": OrderedDict(),
        }
        # count keys by model
        for config in self.available_importers():
            model = self.env["ir.model"]._get(config.model)
            data["report_by_model"][model] = {}
            # be defensive here. At some point
            # we could decide to skip models on demand.
            for k, v in report.get(config.model, {}).items():
                data["report_by_model"][model][k] = len(v)
        return data

    @api.depends("report_data")
    def _compute_report_html(self):
        template = self.env.ref("connector_importer.recordset_report")
        for item in self:
            item.report_html = False
            if not item.report_data:
                continue
            data = item._get_report_html_data()
            item.report_html = template._render(data)

    def _compute_full_report_url(self):
        for item in self:
            item.full_report_url = "/importer/import-recordset/{}".format(item.id)

    def debug_mode(self):
        return self.backend_id.debug_mode or os.getenv("IMPORTER_DEBUG_MODE")

    @api.depends("job_id.state", "record_ids.job_id.state")
    def _compute_jobs_global_state(self):
        for item in self:
            item.jobs_global_state = item._get_global_state()

    @api.model
    def _get_global_state(self):
        res = "no_job"
        if not self.job_id or not self.record_ids:
            return res
        records_job_states = self.mapped("record_ids.job_id.state")
        if all([x == DONE for x in records_job_states]):
            res = DONE
        else:
            # pick the 1st one not done
            not_done = [x for x in records_job_states if x != DONE]
            res = not_done[0] if not_done else res
        return res

    def available_importers(self):
        return self.import_type_id.available_importers()

    def import_recordset(self):
        """This job will import a recordset."""
        with self.backend_id.work_on(self._name) as work:
            importer = work.component(usage="recordset.importer")
            return importer.run(self)

    def run_import(self):
        """queue a job for creating records (import.record items)"""
        job_method = self.with_delay().import_recordset
        if self.debug_mode():
            logger.warning("### DEBUG MODE ACTIVE: WILL NOT USE QUEUE ###")
            job_method = self.import_recordset

        for item in self:
            result = job_method()
            if self.debug_mode():
                # debug mode, no job here: reset it!
                item.write({"job_id": False})
            else:
                # link the job
                item.write({"job_id": result.db_record().id})
        if self.debug_mode():
            # TODO: port this
            # the "after_all" job needs to be fired manually when in debug mode
            # since the event handler in .events.chunk_finished_subscriber
            # cannot estimate when all the chunks have been processed.
            # for model, importer in self.import_type_id.available_models():
            #     import_record_after_all(
            #         session,
            #         self.backend_id.id,
            #         model,
            #     )
            pass

    def generate_report(self):
        self.ensure_one()
        reporter = self.get_source().get_reporter()
        if reporter is None:
            logger.debug("No reporter found...")
            return
        metadata, content = reporter.report_get(self)
        self.write(
            {
                "report_file": base64.encodestring(content.encode()),
                "report_filename": metadata["complete_filename"],
            }
        )
        logger.info(
            ("Report file updated on recordset={}. " "Filename: {}").format(
                self.id, metadata["complete_filename"]
            )
        )

    def _get_importers(self):
        importers = OrderedDict()
        for importer_config in self.available_importers():
            model_record = self.env["ir.model"]._get(importer_config.model)
            importers[model_record] = get_importer_for_config(
                self.backend_id, self._name, importer_config
            )
        return importers

    @api.depends("import_type_id")
    def _compute_docs_html(self):
        template = self.env.ref("connector_importer.recordset_docs")
        for item in self:
            item.docs_html = False
            if isinstance(item.id, models.NewId) or not item.backend_id:
                # Surprise surprise: when editing a new recordset
                # if you hit `configure source` btn
                # the record will be saved but the backend can be null :S
                continue
            importers = item._get_importers()
            data = {"recordset": item, "importers": importers}
            item.docs_html = template._render(data)


# TODO
# @job
# def import_record_after_all(
#         session, backend_id, model_name, last_record_id=None, **kw):
#     """This job will import a record."""
#     # TODO: check this
#     model = 'import.record'
#     env = get_environment(session, model, backend_id)
#     # recordset = None
#     # if last_record_id:
#     #     record = env[model].browse(last_record_id)
#     #     recordset = record.recordset_id
#     importer = get_record_importer(env)
#     return importer.after_all()
