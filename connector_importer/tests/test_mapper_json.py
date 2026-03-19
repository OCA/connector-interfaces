# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo_test_helper import FakeModelLoader

from odoo.tools import DotDict, mute_logger

from ..utils.mapper_utils import to_json
from .common import TestImporterBase


class TestDynamicMapperJson(TestImporterBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        cls.addClassCleanup(cls.loader.restore_registry)
        # fmt: off
        from .fake_models import FakeImportedModel
        cls.loader.update_registry((FakeImportedModel,))
        # fmt: on
        cls.record = cls.env["import.record"].create({"recordset_id": cls.recordset.id})

    def _get_dynamic_mapper(self, options=None):
        opts = {"name": "importer.mapper.dynamic"}
        opts.update(options or {})
        with self.backend.work_on(
            self.record._name,
            components_registry=self.comp_registry,
            options=DotDict({"importer": {}, "mapper": opts}),
        ) as work:
            importer = work.component_by_name(
                "importer.record", model_name="fake.imported.model"
            )
            return importer._get_mapper()

    def test_to_json(self):
        """Serialized JSON and python literals are decoded."""
        self.assertEqual(to_json('{"12": 100.0}'), {"12": 100.0})
        self.assertEqual(to_json("{'12': 100.0}"), {"12": 100.0})
        self.assertEqual(to_json("[1, 2]"), [1, 2])
        self.assertEqual(to_json({"a": 1}), {"a": 1})
        self.assertEqual(to_json([1]), [1])
        self.assertEqual(to_json(""), {})

    def test_to_json_not_valid(self):
        """Invalid values raise unless `raise_if_not_valid` is disabled."""
        with self.assertRaisesRegex(
            ValueError, "Cannot decode JSON value: not-a-json-payload"
        ):
            to_json("not-a-json-payload")
        with self.assertLogs("[importer]", level="WARNING") as logs:
            res = to_json("not-a-json-payload", raise_if_not_valid=False)
        self.assertEqual(res, {})
        self.assertEqual(
            logs.output,
            ["WARNING:[importer]:Cannot decode JSON value: not-a-json-payload"],
        )

    def test_dynamic_mapper_json(self):
        """JSON fields are converted from their serialized value."""
        mapper = self._get_dynamic_mapper()
        expected = {"json_value": {"12": 100.0}}
        rec = {"json_value": '{"12": 100.0}'}
        self.assertEqual(mapper.dynamic_fields(rec), expected)
        rec = {"json_value": "{'12': 100.0}"}
        self.assertEqual(mapper.dynamic_fields(rec), expected)

    def test_dynamic_mapper_json_empty(self):
        """Empty JSON values are converted to an empty dict."""
        mapper = self._get_dynamic_mapper()
        rec = {"json_value": ""}
        self.assertEqual(mapper.dynamic_fields(rec), {"json_value": {}})

    def test_dynamic_mapper_json_not_valid(self):
        """Invalid JSON values raise an error by default."""
        mapper = self._get_dynamic_mapper()
        rec = {"json_value": "not-a-json-payload"}
        with self.assertRaisesRegex(
            ValueError, "Cannot decode JSON value: not-a-json-payload"
        ):
            mapper.dynamic_fields(rec)

    @mute_logger("[importer]")
    def test_dynamic_mapper_json_not_valid_no_raise(self):
        """Invalid JSON values are emptied when configured not to raise."""
        mapper = self._get_dynamic_mapper(
            options={"converter": {"json_value": {"raise_if_not_valid": False}}}
        )
        rec = {"json_value": "not-a-json-payload"}
        self.assertEqual(mapper.dynamic_fields(rec), {"json_value": {}})
