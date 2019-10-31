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
        self.record = self.env["import.record"].create(
            {"recordset_id": self.recordset.id}
        )
        # no jobs thanks (I know, we should test this too at some point :))
        self.backend.debug_mode = True

    def _get_importer(self):
        with self.backend.work_on(
            self.record._name, components_registry=self.comp_registry
        ) as work:
            return work.component(usage="record.importer", model_name="res.partner")

    @mute_logger("[importer]")
    def test_importer_lookup(self):
        importer = self._get_importer()
        self.assertEqual(importer._name, "fake.partner.importer")

    @mute_logger("[importer]")
    def test_importer_required_keys(self):
        importer = self._get_importer()
        required = importer.required_keys()
        self.assertDictEqual(required, {"fullname": ("name",), "id": ("ref",)})

    @mute_logger("[importer]")
    def test_importer_check_missing_none(self):
        importer = self._get_importer()
        values = {"name": "John Doe", "ref": "doe"}
        orig_values = {"fullname": "john doe", "id": "#doe"}
        missing = importer._check_missing("id", "ref", values, orig_values)
        self.assertFalse(missing)

    @mute_logger("[importer]")
    def test_importer_check_missing_source(self):
        importer = self._get_importer()
        values = {"name": "John Doe", "ref": "doe"}
        orig_values = {"fullname": "john doe", "id": "#doe"}
        fullname = orig_values.pop("fullname")
        missing = importer._check_missing("fullname", "name", values, orig_values)
        # name is missing now
        self.assertDictEqual(
            missing, {"message": "MISSING REQUIRED SOURCE KEY=fullname: ref=doe"}
        )
        # drop ref
        orig_values["fullname"] = fullname
        orig_values.pop("id")
        missing = importer._check_missing("id", "ref", values, orig_values)
        # name is missing now
        # `id` missing, so the destination key `ref` is missing
        # so we don't see it in the message
        self.assertDictEqual(
            missing, {"message": "MISSING REQUIRED SOURCE KEY=id: ref=doe"}
        )

    @mute_logger("[importer]")
    def test_importer_check_missing_destination(self):
        importer = self._get_importer()
        values = {"name": "John Doe", "ref": "doe"}
        orig_values = {"fullname": "john doe", "id": "#doe"}
        name = values.pop("name")
        missing = importer._check_missing("fullname", "name", values, orig_values)
        # name is missing now
        self.assertDictEqual(
            missing, {"message": "MISSING REQUIRED DESTINATION KEY=name: ref=doe"}
        )
        # drop ref
        values["name"] = name
        values.pop("ref")
        missing = importer._check_missing("id", "ref", values, orig_values)
        # name is missing now
        # `id` missing, so the destination key `ref` is missing
        # so we don't see it in the message
        self.assertDictEqual(
            missing, {"message": "MISSING REQUIRED DESTINATION KEY=ref"}
        )
