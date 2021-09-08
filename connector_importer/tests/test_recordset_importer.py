# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.tools import mute_logger

from odoo.addons.queue_job.job import Job

from .common import TestImporterBase
from .fake_components import PartnerMapper, PartnerRecordImporter

MOD_PATH = "odoo.addons.connector_importer"
RECORD_MODEL = MOD_PATH + ".models.record.ImportRecord"


class TestRecordsetImporter(TestImporterBase):
    def _get_components(self):
        return [PartnerMapper, PartnerRecordImporter]

    @mute_logger("[importer]")
    @mock.patch("%s.run_import" % RECORD_MODEL)
    def test_recordset_importer(self, mocked_run_inport):
        # generate 100 records
        lines = self._fake_lines(100, keys=("id", "fullname"))
        # source will provide 5x20 chunks
        self._patch_get_source(lines, chunk_size=20)
        # run the recordset importer
        with self.backend.work_on(
            "import.recordset", components_registry=self.comp_registry
        ) as work:
            importer = work.component(usage="recordset.importer")
            self.assertTrue(importer)
            importer.run(self.recordset)
        mocked_run_inport.assert_called()
        # we expect 5 records w/ 20 lines each
        records = self.recordset.get_records()
        self.assertEqual(len(records), 5)
        for rec in records:
            data = rec.get_data()
            self.assertEqual(len(data), 20)
        # order is preserved
        data1 = records[0].get_data()
        self.assertEqual(data1[0]["id"], "id_1")
        self.assertEqual(data1[0]["fullname"], "fullname_1")
        # run it twice and make sure old records are wiped
        # run the recordset importer
        with self.backend.work_on(
            "import.recordset", components_registry=self.comp_registry
        ) as work:
            importer = work.component(usage="recordset.importer")
            self.assertTrue(importer)
            importer.run(self.recordset)
        # we expect 5 records w/ 20 lines each
        records = self.recordset.get_records()
        self.assertEqual(len(records), 5)

    @mute_logger("[importer]")
    def test_job_state(self):
        self.backend.debug_mode = False
        # generate 100 records
        lines = self._fake_lines(100, keys=("id", "fullname"))
        # source will provide 5x20 chunks
        self._patch_get_source(lines, chunk_size=20)
        self.recordset.run_import()
        self.assertFalse(self.recordset.record_ids)
        self.assertEqual(self.recordset.job_id.state, "pending")
        self.assertEqual(self.recordset.job_state, "pending")
        self.assertEqual(self.recordset.jobs_global_state, "no_job")
        Job.load(self.env, self.recordset.job_id.uuid).perform()
        self.assertTrue(self.recordset.record_ids)
        self.assertEqual(self.recordset.jobs_global_state, "pending")
        # perform each job in sequence and check global state
        records = self.recordset.record_ids
        for record in records:
            job = Job.load(self.env, record.job_id.uuid)
            job.set_done()
            job.store()
            expected_state = "pending"
            if record == records[-1]:
                expected_state = "done"
            self.assertEqual(self.recordset.jobs_global_state, expected_state)
