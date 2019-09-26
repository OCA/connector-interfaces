# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import json
import os

from odoo import api, fields, models

from odoo.addons.queue_job.job import job

from ..log import logger
from .job_mixin import JobRelatedMixin


class ImportRecord(models.Model, JobRelatedMixin):
    """Data to be imported.

    An import record contains what you are actually importing.

    Depending on backend settings you gonna have one or more source records
    stored as JSON data into `jsondata` field.

    No matter where you are importing from (CSV, SQL, etc)
    the importer machinery will:

    * retrieve the models to import and their importer
    * process all records and import them
    * update recordset info

    When the importer will run, it will read all the records,
    convert them using connector mappers and do the import.
    """

    _name = "import.record"
    _description = "Import record"
    _order = "id"
    _backend_type = "import_backend"

    date = fields.Datetime("Import date", default=fields.Datetime.now)
    # This field holds the whole bare data to import from the external source
    # hence it can be huge. For this reason we store it in an attachment.
    jsondata_file = fields.Binary(attachment=True)
    recordset_id = fields.Many2one("import.recordset", string="Recordset")
    backend_id = fields.Many2one(
        "import.backend",
        string="Backend",
        related="recordset_id.backend_id",
        readonly=True,
    )

    def unlink(self):
        # inheritance of non-model mixin does not work w/out this
        return super().unlink()

    @api.depends("date")
    def _compute_name(self):
        for item in self:
            names = [item.date]
            item.name = " / ".join([_f for _f in names if _f])

    def set_data(self, adict):
        self.ensure_one()
        jsondata = json.dumps(adict)
        self.jsondata_file = base64.b64encode(bytes(jsondata, "utf-8"))

    def get_data(self):
        self.ensure_one()
        jsondata = None
        if self.jsondata_file:
            raw_data = base64.b64decode(self.jsondata_file).decode("utf-8")
            jsondata = json.loads(raw_data)
        return jsondata or {}

    def debug_mode(self):
        self.ensure_one()
        return self.backend_id.debug_mode or os.environ.get("IMPORTER_DEBUG_MODE")

    @job
    def import_record(self, component_name, model_name, is_last_importer=True):
        """This job will import a record.

        :param component_name: name of the importer component to use
        :param model_name: name of the model to import
        :param is_last_importer: flag for last importer of the recordset
        """
        kwargs = {}
        if self.env.context.get("test_components_registry"):
            kwargs["components_registry"] = self.env.context["test_components_registry"]
        with self.backend_id.work_on(self._name, **kwargs) as work:
            importer = work.component_by_name(component_name, model_name=model_name)
            return importer.run(self, is_last_importer=is_last_importer)

    def run_import(self):
        """ queue a job for importing data stored in to self
        """
        use_job = self.recordset_id.import_type_id.use_job
        job_method = self.with_delay().import_record
        if self.debug_mode():
            logger.warn("### DEBUG MODE ACTIVE: WILL NOT USE QUEUE ###")
        if self.debug_mode() or not use_job:
            job_method = self.import_record
        _result = {}
        for item in self:
            # we create a record and a job for each model name
            # that needs to be imported
            for (
                model,
                importer,
                is_last_importer,
            ) in item.recordset_id.available_models():
                # TODO: grab component from config
                result = job_method(importer, model, is_last_importer=is_last_importer)
                _result[model] = result
                if self.debug_mode() or not use_job:
                    # debug mode, no job here: reset it!
                    item.write({"job_id": False})
                else:
                    # FIXME: we should have a o2m here otherwise
                    # w/ multiple importers for the same record
                    # we keep the reference on w/ the last job.
                    item.write({"job_id": result.db_record().id})
        return _result
