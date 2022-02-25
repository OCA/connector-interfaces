# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, api, exceptions, fields, models

cleanup_logger = logging.getLogger("[recordset-cleanup]")

BACKEND_VERSIONS = [("1.0", "Version 1.0")]


class ImporterBackend(models.Model):
    _name = "import.backend"
    _description = "Importer Backend"
    _inherit = ["connector.backend", "cron.mixin"]

    @api.model
    def _select_version(self):
        """Available versions

        Can be inherited to add custom versions.
        """
        return BACKEND_VERSIONS

    name = fields.Char(required=True)
    version = fields.Selection(selection="_select_version", required=True)
    recordset_ids = fields.One2many(
        "import.recordset", "backend_id", string="Record Sets"
    )
    # cron stuff
    cron_master_recordset_id = fields.Many2one(
        "import.recordset",
        string="Master recordset",
        help=(
            "If an existing recordset is selected "
            "it will be used to create a new recordset "
            "each time the cron runs. "
            "\nIn this way you can keep every import session isolated. "
            "\nIf none, all recordsets will run."
        ),
    )
    cron_cleanup_keep = fields.Integer(
        help=(
            "If this value is greater than 0 "
            "a cron will cleanup old recordsets "
            "and keep only the latest N records matching this value."
        ),
    )
    notes = fields.Text()
    debug_mode = fields.Boolean(
        "Debug mode?",
        help=(
            "Enabling debug mode causes the import to run "
            "in real time, without using any job queue. "
            "Make sure you don't do this in production!"
        ),
    )
    job_running = fields.Boolean(
        compute="_compute_job_running",
        help="Tells you if a job is running for this backend.",
        readonly=True,
    )

    def unlink(self):
        """Prevent delete if jobs are running."""
        for item in self:
            item._check_delete()
        return super().unlink()

    def _check_delete(self):
        if not self.debug_mode and self.job_running:
            raise exceptions.Warning(_("You must complete the job first!"))

    def _compute_job_running(self):
        for item in self:
            running = False
            for recordset in self.recordset_ids:
                if recordset.has_job() and not recordset.job_done():
                    running = True
                    break
                for record in recordset.record_ids:
                    if record.has_job() and not record.job_done():
                        running = True
                        break
            item.job_running = running

    @api.model
    def run_cron(self, backend_id):
        # required by cron mixin
        self.browse(backend_id).run_all()

    def run_all(self):
        """Run all recordset imports."""
        self.ensure_one()
        recordsets = self.recordset_ids
        if self.cron_master_recordset_id:
            # clone and use it to run
            recordsets = self.cron_master_recordset_id.copy()
        for recordset in recordsets:
            recordset.run_import()

    @api.model
    def cron_cleanup_recordsets(self):
        """Delete obsolete recordsets.

        If you are running imports via cron and you create one recorset
        per each run then you might end up w/ tons of old recordsets.

        You can use `cron_cleanup_keep` to enable auto-cleanup.
        Here we lookup for backends w/ this settings
        and keep only latest recordsets.
        """
        cleanup_logger.info("Looking for recorsets to cleanup.")
        backends = self.search([("cron_cleanup_keep", ">", 0)])
        to_clean = self.env["import.recordset"]
        for backend in backends:
            if len(backend.recordset_ids) <= backend.cron_cleanup_keep:
                continue
            to_keep = backend.recordset_ids.sorted(
                lambda x: x.create_date, reverse=True
            )[: backend.cron_cleanup_keep]
            # always keep this
            to_keep |= backend.cron_master_recordset_id
            to_clean = backend.recordset_ids - to_keep
        if to_clean:
            msg = "Cleaning up {}".format(",".join(to_clean.mapped("name")))
            cleanup_logger.info(msg)
            to_clean.unlink()
        else:
            cleanup_logger.info("Nothing to do.")

    def button_complete_jobs(self):
        """Set all jobs to "completed" state."""
        self.ensure_one()
        for recordset in self.recordset_ids:
            for record in recordset.record_ids:
                if record.has_job() and not record.job_done():
                    record.job_id.button_done()
            if recordset.has_job() and not recordset.job_done():
                recordset.job_id.button_done()
