# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tools import mute_logger

from .test_recordset_importer import TestImporterBase

# TODO: really annoying when running tests. Remove or find a better way
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.ERROR)
logging.getLogger("passlib.registry").setLevel(logging.ERROR)

MOD_PATH = "odoo.addons.connector_importer"
RECORD_MODEL = MOD_PATH + ".models.record.ImportRecord"


class TestRecordImporter(TestImporterBase):
    def _setup_records(self):
        super()._setup_records()
        # The components registry will be handled by the
        # `import.record.import_record()' method when initializing its
        # WorkContext
        self.record = (
            self.env["import.record"]
            .with_context(test_components_registry=self.comp_registry)
            .create({"recordset_id": self.recordset.id})
        )
        # no jobs thanks (I know, we should test this too at some point :))
        self.backend.debug_mode = True

    @mute_logger("[importer]")
    def test_importer_create(self):
        # generate 10 records
        lines = self._fake_lines(10, keys=("id", "fullname"))
        # set them on record
        self.record.set_data(lines)
        res = self.record.run_import()
        # in any case we'll get this per each model if the import is not broken
        self.assertEqual(res, {"res.partner": "ok"})
        report = self.recordset.get_report()
        self.assertEqual(len(report["res.partner"]["created"]), 10)
        self.assertEqual(len(report["res.partner"]["errored"]), 0)
        self.assertEqual(len(report["res.partner"]["updated"]), 0)
        self.assertEqual(len(report["res.partner"]["skipped"]), 0)
        self.assertEqual(
            self.env["res.partner"].search_count([("ref", "like", "id_%")]), 10
        )

    @mute_logger("[importer]")
    def test_importer_skip(self):
        # generate 10 records
        lines = self._fake_lines(10, keys=("id", "fullname"))
        # make a line skip
        lines[0].pop("fullname")
        lines[1].pop("id")
        # set them on record
        self.record.set_data(lines)
        res = self.record.run_import()
        # in any case we'll get this per each model if the import is not broken
        self.assertEqual(res, {"res.partner": "ok"})
        report = self.recordset.get_report()
        self.assertEqual(len(report["res.partner"]["created"]), 8)
        self.assertEqual(len(report["res.partner"]["errored"]), 0)
        self.assertEqual(len(report["res.partner"]["updated"]), 0)
        self.assertEqual(len(report["res.partner"]["skipped"]), 2)
        skipped_msg1 = report["res.partner"]["skipped"][0]["message"]
        skipped_msg2 = report["res.partner"]["skipped"][1]["message"]
        self.assertEqual(skipped_msg1, "MISSING REQUIRED SOURCE KEY=fullname: ref=id_1")
        # `id` missing, so the destination key `ref` is missing
        # so we don't see it in the message
        self.assertEqual(skipped_msg2, "MISSING REQUIRED SOURCE KEY=id")
        self.assertEqual(
            self.env["res.partner"].search_count([("ref", "like", "id_%")]), 8
        )

    @mute_logger("[importer]")
    def test_importer_update(self):
        # generate 10 records
        lines = self._fake_lines(10, keys=("id", "fullname"))
        self.record.set_data(lines)
        res = self.record.run_import()
        # in any case we'll get this per each model if the import is not broken
        self.assertEqual(res, {"res.partner": "ok"})
        report = self.recordset.get_report()
        self.assertEqual(len(report["res.partner"]["created"]), 10)
        self.assertEqual(len(report["res.partner"]["updated"]), 0)
        # now run it a second time
        # but we must flush the old report which is usually done
        # by the recordset importer
        self.recordset.set_report({}, reset=True)
        res = self.record.run_import()
        report = self.recordset.get_report()
        self.assertEqual(len(report["res.partner"]["created"]), 0)
        self.assertEqual(len(report["res.partner"]["updated"]), 10)
        # now run it a second time
        # but we set `override existing` false
        self.recordset.set_report({}, reset=True)
        report = self.recordset.override_existing = False
        res = self.record.run_import()
        report = self.recordset.get_report()
        self.assertEqual(len(report["res.partner"]["created"]), 0)
        self.assertEqual(len(report["res.partner"]["updated"]), 0)
        self.assertEqual(len(report["res.partner"]["skipped"]), 10)
        skipped_msg1 = report["res.partner"]["skipped"][0]["message"]
        self.assertEqual(skipped_msg1, "ALREADY EXISTS: ref=id_1")
