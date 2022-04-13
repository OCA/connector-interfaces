# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tools import DotDict, mute_logger

from .common import TestImporterBase


class TestRecordImporter(TestImporterBase):
    @classmethod
    def _setup_records(cls):
        res = super()._setup_records()
        cls.record = cls.env["import.record"].create({"recordset_id": cls.recordset.id})
        return res

    def _get_components(self):
        from .fake_components import PartnerMapper, PartnerRecordImporter

        return [PartnerRecordImporter, PartnerMapper]

    def _get_importer(self):
        with self.backend.work_on(
            self.record._name,
            components_registry=self.comp_registry,
            options=DotDict({"importer": {}, "mapper": {}}),
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

    def test_importer_get_mapper(self):
        importer = self._get_importer()
        mapper = importer._get_mapper()
        self.assertEqual(mapper._name, "fake.partner.mapper")
        importer.work.options["mapper"] = {"name": "importer.mapper.dynamic"}
        mapper = importer._get_mapper()
        self.assertEqual(mapper._name, "importer.mapper.dynamic")
        importer.work.options["mapper"] = {"usage": "importer.dynamicmapper"}
        mapper = importer._get_mapper()
        self.assertEqual(mapper._name, "importer.mapper.dynamic")
        # name via class attribute have precedence
        importer._mapper_name = "fake.partner.mapper"
        mapper = importer._get_mapper()
        self.assertEqual(mapper._name, "fake.partner.mapper")
