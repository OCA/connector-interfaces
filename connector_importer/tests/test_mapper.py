# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tools import DotDict

from .common import TestImporterBase

MOD_PATH = "odoo.addons.connector_importer"
RECORD_MODEL = MOD_PATH + ".models.record.ImportRecord"


class TestRecordsetImporter(TestImporterBase):
    @classmethod
    def _setup_records(cls):
        res = super()._setup_records()
        cls.record = cls.env["import.record"].create({"recordset_id": cls.recordset.id})
        return res

    def _get_importer(self, options=None):
        options = options or DotDict({"importer": {}, "mapper": {}})
        with self.backend.work_on(
            self.record._name,
            components_registry=self.comp_registry,
            options=options,
        ) as work:
            return work.component_by_name("importer.record", model_name="res.partner")

    def _get_mapper(self, options=None):
        return self._get_importer(options=options)._get_mapper()

    def _get_dynamyc_mapper(self, options=None):
        opts = {"name": "importer.mapper.dynamic"}
        opts.update(options or {})
        return self._get_mapper(options=DotDict({"importer": {}, "mapper": opts}))

    # TODO: test basic mapper and automapper too

    def test_dynamic_mapper_clean_record(self):
        mapper = self._get_dynamyc_mapper()
        rec = {
            "name": "John Doe",
            "ref": "12345",
            "_foo": "something",
            "some_one": 1,
            "some_two": 2,
        }
        expected = {
            "name": "John Doe",
            "ref": "12345",
            "some_one": 1,
            "some_two": 2,
        }
        self.assertEqual(mapper._clean_record(rec), expected)
        # Whitelist
        mapper = self._get_dynamyc_mapper(
            options=dict(source_key_whitelist=["name", "ref"])
        )
        expected = {
            "name": "John Doe",
            "ref": "12345",
        }
        self.assertEqual(mapper._clean_record(rec), expected)
        # Prefix
        mapper = self._get_dynamyc_mapper(options=dict(source_key_prefix="some_"))
        expected = {
            "some_one": 1,
            "some_two": 2,
        }
        self.assertEqual(mapper._clean_record(rec), expected)

    def test_dynamic_mapper_non_mapped_keys(self):
        mapper = self._get_dynamyc_mapper()
        rec = {
            "name": "John Doe",
            "ref": "12345",
            "_foo": "something",
            "some_one": 1,
            "some_two": 2,
        }
        clean_rec = mapper._clean_record(rec)
        expected = (
            "name",
            "ref",
            "some_one",
            "some_two",
        )
        self.assertEqual(sorted(mapper._non_mapped_keys(clean_rec)), sorted(expected))

    def test_dynamic_mapper_values(self):
        mapper = self._get_dynamyc_mapper()
        rec = {}
        expected = {}
        self.assertEqual(mapper.dynamic_fields(rec), expected)
        mapper = self._get_dynamyc_mapper()
        rec = {"name": "John Doe", "ref": "12345"}
        expected = rec.copy()
        self.assertEqual(mapper.dynamic_fields(rec), expected)
        mapper = self._get_dynamyc_mapper()
        cat = self.env.ref("base.res_partner_category_0")
        rec = {
            "name": "John Doe",
            "ref": "12345",
            "xid::parent_id": "base.res_partner_10",
            "category_id": cat.name,
        }
        expected = {
            "name": "John Doe",
            "ref": "12345",
            "parent_id": self.env.ref("base.res_partner_10").id,
            "category_id": [(6, 0, cat.ids)],
        }
        self.assertEqual(mapper.dynamic_fields(rec), expected)

    def test_dynamic_mapper_skip_empty(self):
        rec = {
            "name": "John Doe",
            "ref": "",
        }
        # Whitelist
        expected = {
            "name": "John Doe",
        }
        mapper = self._get_dynamyc_mapper(options=dict(source_key_empty_skip=["ref"]))
        self.assertEqual(mapper.dynamic_fields(rec), expected)
