# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import RecordCapturer
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
        options = options or {"importer": {}, "mapper": {}}
        with self.backend.work_on(
            self.record._name,
            components_registry=self.comp_registry,
            options=DotDict(options),
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
        # Blacklist
        mapper = self._get_dynamyc_mapper(options=dict(source_key_blacklist=["ref"]))
        expected = {
            "name": "John Doe",
            "some_one": 1,
            "some_two": 2,
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
        categs = self.env.ref("base.res_partner_category_0") + self.env.ref(
            "base.res_partner_category_2"
        )
        rec = {
            "name": "John Doe",
            "ref": "12345",
            "xid::parent_id": "base.res_partner_10",
            "xid::category_id": "base.res_partner_category_0,base.res_partner_category_2",
            "title_id": "Doctor",
        }
        expected = {
            "name": "John Doe",
            "ref": "12345",
            "parent_id": self.env.ref("base.res_partner_10").id,
            "category_id": [(6, 0, categs.ids)],
        }
        self.assertEqual(mapper.dynamic_fields(rec), expected)

    def test_dynamic_mapper_values_with_prefix(self):
        mapper = self._get_dynamyc_mapper(options=dict(source_key_prefix="foo."))
        rec = {}
        expected = {}
        categs = self.env.ref("base.res_partner_category_0") + self.env.ref(
            "base.res_partner_category_2"
        )
        rec = {
            "foo.name": "John Doe",
            "ref": "12345",
            "xid::foo.parent_id": "base.res_partner_10",
            "xid::foo.category_id": "base.res_partner_category_0,base.res_partner_category_2",
            "title_id": "Doctor",
        }
        expected = {
            "name": "John Doe",
            "parent_id": self.env.ref("base.res_partner_10").id,
            "category_id": [(6, 0, categs.ids)],
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

    def test_rel_create_if_missing(self):
        opts = {
            "parent_id": {"create_missing": True},
            "category_id": {"create_missing": True},
        }
        mapper = self._get_dynamyc_mapper(options=dict(converter=opts))
        rec = {
            "name": "John Doe",
            "ref": "12345",
            "parent_id": "Parent of J. Doe",
            "category_id": "New category",
        }
        with RecordCapturer(
            self.env["res.partner"].sudo(), []
        ) as partner_capt, RecordCapturer(
            self.env["res.partner.category"].sudo(), []
        ) as cat_capt:
            res = mapper.dynamic_fields(rec)
            parent = partner_capt.records
            cat = cat_capt.records
            self.assertEqual(parent.name, "Parent of J. Doe")
            self.assertEqual(cat.name, "New category")
            self.assertEqual(res["parent_id"], parent.id)
            self.assertEqual(res["category_id"], [(6, 0, [cat.id])])

    def test_dynamic_mapper_rename_keys(self):
        rec = {
            "another_name": "John Doe",
        }
        # Whitelist
        expected = {
            "name": "John Doe",
        }
        mapper = self._get_dynamyc_mapper(
            options=dict(source_key_rename={"another_name": "name"})
        )
        self.assertEqual(mapper.dynamic_fields(rec), expected)
