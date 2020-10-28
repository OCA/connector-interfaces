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
        self.record = (
            self.env["import.record"]
            .with_context(test_components_registry=self.comp_registry)
            .create({"recordset_id": self.recordset.id})
        )

    def _get_components(self):
        from .fake_components import (
            PartnerMapperXMLID,
            PartnerRecordImporterXMLID,
        )

        return [
            PartnerMapperXMLID,
            PartnerRecordImporterXMLID,
        ]

    @mute_logger("[importer]")
    def test_importer_create(self):
        self.import_type.write({"settings": "res.partner::fake.partner.importer.xmlid"})

        # generate 10 records
        count = 10
        lines = self._fake_lines(count, keys=("id", "fullname"))
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
        # Check XML-IDs
        for i in range(1, count + 1):
            partner = self.env.ref(
                "__import__.id_{}".format(i), raise_if_not_found=False
            )
            self.assertTrue(partner)
