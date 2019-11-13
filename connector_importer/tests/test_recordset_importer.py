# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.component.tests import common

from ..utils.import_utils import gen_chunks
from .fake_components import PartnerMapper, PartnerRecordImporter

MOD_PATH = "odoo.addons.connector_importer"
RECORD_MODEL = MOD_PATH + ".models.record.ImportRecord"


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


class TestImporterBase(common.TransactionComponentRegistryCase):
    def setUp(self):
        super().setUp()
        self._setup_records()
        self._load_module_components("connector_importer")
        self._build_components(*self._get_components())

    def _get_components(self):
        return [PartnerMapper, PartnerRecordImporter]

    def _setup_records(self):
        self.backend = self.env["import.backend"].create(
            {"name": "Foo", "version": "1.0"}
        )
        itype = self.env["import.type"].create(
            {
                "name": "Fake",
                "key": "fake",
                "settings": "res.partner::fake.partner.importer",
            }
        )
        self.recordset = self.env["import.recordset"].create(
            {"backend_id": self.backend.id, "import_type_id": itype.id}
        )

    def _patch_get_source(self, lines, chunk_size=5):
        self.env["import.recordset"]._patch_method(
            "get_source", lambda x: MockedSource(lines, chunk_size=chunk_size)
        )

    def _fake_lines(self, count, keys=None):
        return fake_lines(count, keys=keys or [])


class TestRecordsetImporter(TestImporterBase):
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
