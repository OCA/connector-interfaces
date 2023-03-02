# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import io
import logging

import odoo.tests.common as common
from odoo.modules.module import get_resource_path

from odoo.addons.component.tests.common import TransactionComponentRegistryCase

from ..utils.import_utils import gen_chunks

# TODO: really annoying when running tests. Remove or find a better way
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.ERROR)
logging.getLogger("passlib.registry").setLevel(logging.ERROR)


def _load_filecontent(module, filepath, mode="r"):
    path = get_resource_path(module, filepath)
    with io.open(path, mode) as fd:
        return fd.read()


class BaseTestCase(common.TransactionCase):
    @staticmethod
    def load_filecontent(*args, **kwargs):
        return _load_filecontent(*args, **kwargs)


class MockedSource(object):
    """A fake source for recordsets."""

    lines = []
    chunks_size = 5

    def __init__(self, lines, chunk_size=5):
        self.lines = lines
        self.chunks_size = chunk_size

    def get_lines(self):
        return gen_chunks(self.lines, self.chunks_size)


def fake_lines(count, keys):
    """Generate importable fake lines."""
    res = []
    _item = {}.fromkeys(keys, "")
    for i in range(1, count + 1):
        item = _item.copy()
        for k in keys:
            item[k] = "{}_{}".format(k, i)
        item["_line_nr"] = i
        res.append(item)
    return res


class TestImporterMixin(object):
    def _setup_components(self):
        for mod in self._get_component_modules():
            self._load_module_components(mod)
        self._build_components(*self._get_components())

    def _get_component_modules(self):
        return ["connector_importer"]

    def _get_components(self):
        return []

    @classmethod
    def _setup_records(cls):
        cls.backend = cls.env["import.backend"].create(
            # no jobs thanks (I know, we should test this too at some point :))
            {"name": "Foo", "version": "1.0", "debug_mode": True}
        )
        cls.import_type = cls.env["import.type"].create(
            {
                "name": "Fake",
                "key": "fake",
                "options": """
- model: res.partner
  importer: fake.partner.importer
                """,
            }
        )
        cls.recordset = cls.env["import.recordset"].create(
            {"backend_id": cls.backend.id, "import_type_id": cls.import_type.id}
        )

    def _patch_get_source(self, lines, chunk_size=5):
        self.env["import.recordset"]._patch_method(
            "get_source", lambda x: MockedSource(lines, chunk_size=chunk_size)
        )

    def _fake_lines(self, count, keys=None):
        return fake_lines(count, keys=keys or [])

    @staticmethod
    def load_filecontent(*args, **kwargs):
        return _load_filecontent(*args, **kwargs)


class TestImporterBase(TransactionComponentRegistryCase, TestImporterMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_registry(cls)
        cls._setup_records()

    def setUp(self):
        super().setUp()
        self._setup_components()

    @classmethod
    def tearDownClass(cls):
        cls._teardown_registry(cls)
        return super().tearDownClass()
