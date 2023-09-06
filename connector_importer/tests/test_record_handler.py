# Author: Simone Orsi
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tools import DotDict

from .common import TestImporterBase

values = {
    "name": "John",
    "age": 40,
}
orig_values = {
    "Name": "John  ",
    "Age": "40",
}


class TestRecordImporter(TestImporterBase):
    @classmethod
    def _setup_records(cls):  # pylint: disable=missing-return
        super()._setup_records()
        cls.record = cls.env["import.record"].create({"recordset_id": cls.recordset.id})

    def _get_components(self):
        from .fake_components import PartnerMapper, PartnerRecordImporter

        return [PartnerRecordImporter, PartnerMapper]

    def _get_handler(self):
        with self.backend.work_on(
            self.record._name,
            components_registry=self.comp_registry,
            options=DotDict({"record_handler": {}}),
        ) as work:
            return work.component(usage="odoorecord.handler", model_name="res.partner")

    def test_match_domain(self):
        handler = self._get_handler()
        domain = handler._odoo_find_domain_from_options(values, orig_values)
        self.assertEqual(domain, [])
        handler.work.options["record_handler"] = {
            "match_domain": "[('name', '=', values['name']), ('age', '=', orig_values['Age'])]"
        }
        domain = handler._odoo_find_domain_from_options(values, orig_values)
        self.assertEqual(
            domain, [("name", "=", values["name"]), ("age", "=", orig_values["Age"])]
        )

    def test_unique_key_domain(self):
        handler = self._get_handler()
        handler.unique_key = "nowhere"
        with self.assertRaises(ValueError):
            domain = handler._odoo_find_domain_from_unique_key(values, orig_values)
        handler.unique_key = "name"
        domain = handler._odoo_find_domain_from_unique_key(values, orig_values)
        self.assertEqual(domain, [("name", "=", values["name"])])
        handler.unique_key = "Name"
        domain = handler._odoo_find_domain_from_unique_key(values, orig_values)
        self.assertEqual(domain, [("Name", "=", orig_values["Name"])])

    def test_find_domain(self):
        handler = self._get_handler()
        handler.unique_key = "age"
        domain = handler.odoo_find_domain(values, orig_values)
        self.assertEqual(domain, [("age", "=", values["age"])])
        handler.work.options["record_handler"] = {
            "match_domain": "[('name', '=', values['name']), ('age', '=', values['age'])]"
        }
        domain = handler.odoo_find_domain(values, orig_values)
        self.assertEqual(
            domain, [("name", "=", values["name"]), ("age", "=", values["age"])]
        )
