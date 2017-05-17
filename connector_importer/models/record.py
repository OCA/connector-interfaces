# -*- coding: utf-8 -*-
# Author: Simone Orsi
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import os

from odoo import models, fields, api
from odoo.addons.queue_job.job import job

from .recordset import get_record_importer
from .job_mixin import JobRelatedMixin
from ..log import logger


class ImportRecord(models.Model, JobRelatedMixin):
    _name = 'import.record'
    _description = 'Import record'
    _order = 'date DESC'
    _backend_type = 'import_backend'

    date = fields.Datetime(
        'Import date',
        default=fields.Date.context_today,
    )
    jsondata = fields.Text('JSON Data')
    recordset_id = fields.Many2one(
        'import.recordset',
        string='Recordset'
    )
    backend_id = fields.Many2one(
        'import.backend',
        string='Backend',
        related='recordset_id.backend_id',
        readonly=True,
    )

    @api.multi
    def unlink(self):
        # inheritance of non-model mixin does not work w/out this
        return super(ImportRecord, self).unlink()

    @api.multi
    @api.depends('date')
    def _compute_name(self):
        for item in self:
            names = [
                item.date,
            ]
            item.name = ' / '.join(filter(None, names))

    @api.multi
    def set_data(self, adict):
        self.ensure_one()
        self.jsondata = json.dumps(adict)

    @api.multi
    def get_data(self):
        self.ensure_one()
        return json.loads(self.jsondata or '{}')

    @api.multi
    def debug_mode(self):
        self.ensure_one()
        return self.backend_id.debug_mode or \
            os.environ.get('IMPORTER_DEBUG_MODE')

    @job
    def import_record(self, dest_model_name, importer_dotted_path=None, **kw):
        """This job will import a record."""

        with self.backend_id.get_environment(dest_model_name) as env:
            importer = get_record_importer(
                env, importer_dotted_path=importer_dotted_path)
            return importer.run(self)

    @api.multi
    def run_import(self):
        """ queue a job for importing data stored in to self
        """
        job_method = self.with_delay().import_record
        if self.debug_mode():
            logger.warn('### DEBUG MODE ACTIVE: WILL NOT USE QUEUE ###')
            job_method = self.import_record
        for item in self:
            # we create a record and a job for each model name
            # that needs to be imported
            for model, importer in item.recordset_id.available_models():
                job = job_method(model, importer_dotted_path=importer)
                if job:
                    # link the job
                    item.write({'job_id': job.db_record().id})
                if self.debug_mode():
                    # debug mode, no job here: reset it!
                    item.write({'job_id': False})
