# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tools import mute_logger

from .common import TestImporterBase

MOD_PATH = "odoo.addons.connector_importer"
RECORD_MODEL = MOD_PATH + ".models.record.ImportRecord"
LOGGERS_TO_MUTE = (
    "[importer]",
    "odoo.addons.queue_job.utils",
)


class TestRecordImporter(TestImporterBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # generate 10 records
        cls.fake_lines = cls._fake_lines(cls, 10, keys=("id", "fullname"))

    def setUp(self):
        super().setUp()
        # The components registry will be handled by the
        # `import.record.import_record()' method when initializing its
        # WorkContext
        self.record = self.env["import.record"].create(
            {"recordset_id": self.recordset.id}
        )

    def _get_components(self):
        from .fake_components import PartnerMapper, PartnerRecordImporter

        return [PartnerRecordImporter, PartnerMapper]

    @mute_logger(*LOGGERS_TO_MUTE)
    def test_importer_create(self):
        # set them on record
        self.record.set_data(self.fake_lines)
        res = self.record.run_import()
        report = self.recordset.get_report()
        # in any case we'll get this per each model if the import is not broken
        model = "res.partner"
        expected = {
            model: {"created": 10, "errored": 0, "updated": 0, "skipped": 0},
        }
        result = res[model]
        self.assertEqual(result, expected[model])
        for k, v in expected[model].items():
            self.assertEqual(len(report[model][k]), v)
        self.assertEqual(self.env[model].search_count([("ref", "like", "id_%")]), 10)

    @mute_logger("[importer]")
    def test_importer_create_debug_mode_off(self):
        # set them on record
        self.record.set_data(self.fake_lines)
        self.record.backend_id.debug_mode = False
        res = self.record._run_import(use_job=True)
        self.recordset.get_report()
        # in any case we'll get this per each model if the import is not broken
        model = "res.partner"
        expected = {
            model: {"created": 10, "errored": 0, "updated": 0, "skipped": 0},
        }
        delayable = res[model]
        result = delayable.perform()
        self.assertEqual(result, expected[model])
        result = {model: result}
        for k, v in expected[model].items():
            self.assertEqual(result[model][k], v)
        self.assertEqual(self.env[model].search_count([("ref", "like", "id_%")]), 10)

    @mute_logger(*LOGGERS_TO_MUTE)
    def test_importer_skip(self):
        # generate 10 records
        lines = self._fake_lines(10, keys=("id", "fullname"))
        # make a line skip
        lines[0].pop("fullname")
        lines[1].pop("id")
        # set them on record
        self.record.set_data(lines)
        res = self.record.run_import()
        report = self.recordset.get_report()
        model = "res.partner"
        expected = {model: {"created": 8, "errored": 0, "updated": 0, "skipped": 2}}
        result = res[model]
        self.assertEqual(result, expected[model])
        for k, v in expected[model].items():
            self.assertEqual(len(report[model][k]), v)
        skipped_msg1 = report[model]["skipped"][0]["message"]
        skipped_msg2 = report[model]["skipped"][1]["message"]
        self.assertEqual(skipped_msg1, "MISSING REQUIRED SOURCE KEY=fullname: ref=id_1")
        # `id` missing, so the destination key `ref` is missing
        # so we don't see it in the message
        self.assertEqual(skipped_msg2, "MISSING REQUIRED SOURCE KEY=id")
        self.assertEqual(self.env[model].search_count([("ref", "like", "id_%")]), 8)

    @mute_logger(*LOGGERS_TO_MUTE)
    def test_importer_update(self):
        # generate 10 records
        lines = self._fake_lines(10, keys=("id", "fullname"))
        self.record.set_data(lines)
        res = self.record.run_import()
        report = self.recordset.get_report()
        model = "res.partner"
        expected = {model: {"created": 10, "errored": 0, "updated": 0, "skipped": 0}}
        result = res[model]
        self.assertEqual(result, expected[model])
        for k, v in expected[model].items():
            self.assertEqual(len(report[model][k]), v)
        # now run it a second time
        # but we must flush the old report which is usually done
        # by the recordset importer
        self.recordset.set_report({}, reset=True)
        res = self.record.run_import()
        report = self.recordset.get_report()
        expected = {model: {"created": 0, "errored": 0, "updated": 10, "skipped": 0}}
        result = res[model]
        self.assertEqual(result, expected[model])
        for k, v in expected[model].items():
            self.assertEqual(len(report[model][k]), v)
        # now run it a second time
        # but we set `override existing` false
        self.recordset.set_report({}, reset=True)
        report = self.recordset.override_existing = False
        res = self.record.run_import()
        report = self.recordset.get_report()
        expected = {model: {"created": 0, "errored": 0, "updated": 0, "skipped": 10}}
        result = res[model]
        self.assertEqual(result, expected[model])
        for k, v in expected[model].items():
            self.assertEqual(len(report[model][k]), v)
        skipped_msg1 = report[model]["skipped"][0]["message"]
        self.assertEqual(skipped_msg1, "ALREADY EXISTS: ref=id_1")
