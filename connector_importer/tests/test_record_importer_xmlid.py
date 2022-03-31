# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tools import mute_logger

from .common import TestImporterBase


class TestRecordImporterXMLID(TestImporterBase):
    def setUp(self):
        super().setUp()
        # The components registry will be handled by the
        # `import.record.import_record()' method when initializing its
        # WorkContext
        self.record = self.env["import.record"].create(
            {"recordset_id": self.recordset.id}
        )

    def _get_components(self):
        from .fake_components import PartnerMapperXMLID, PartnerRecordImporterXMLID

        return [
            PartnerMapperXMLID,
            PartnerRecordImporterXMLID,
        ]

    @mute_logger("[importer]")
    def test_importer_create(self):
        self.import_type.write(
            {
                "options": """
- model: res.partner
  importer: fake.partner.importer.xmlid
                """
            }
        )
        # generate 10 records
        count = 10
        lines = self._fake_lines(count, keys=("id", "fullname"))
        # set them on record
        self.record.set_data(lines)
        res = self.record.run_import()
        report = self.recordset.get_report()
        model = "res.partner"
        expected = {model: {"created": 10, "errored": 0, "updated": 0, "skipped": 0}}
        self.assertEqual(res, expected)
        for k, v in expected[model].items():
            self.assertEqual(len(report[model][k]), v)
        self.assertEqual(self.env[model].search_count([("ref", "like", "id_%")]), 10)
        # Check XML-IDs
        for i in range(1, count + 1):
            partner = self.env.ref(
                "__import__.id_{}".format(i), raise_if_not_found=False
            )
            self.assertTrue(partner)
