# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import odoo.tests.common as common


class TestRecordset(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.recordset_model = cls.env["import.recordset"]
        cls.backend_model = cls.env["import.backend"]
        cls.type_model = cls.env["import.type"]
        cls.bknd = cls._create_backend()
        cls.itype = cls._create_type()
        cls.recordset = cls._create_recordset()

    @classmethod
    def _create_backend(cls):
        return cls.backend_model.create({"name": "Foo", "version": "1.0"})

    @classmethod
    def _create_type(cls):
        return cls.type_model.create(
            {
                "name": "Ok",
                "key": "ok",
                "options": """
- model: res.partner
  importer: partner.importer
            """,
            }
        )

    @classmethod
    def _create_recordset(cls):
        return cls.recordset_model.create(
            {"backend_id": cls.bknd.id, "import_type_id": cls.itype.id}
        )

    def test_recordset_name(self):
        self.assertEqual(
            self.recordset.name,
            "#" + str(self.recordset.id),
        )

    def test_available_importers(self):
        """Available models are propagated from import type."""
        self.assertEqual(
            tuple(self.recordset.available_importers()),
            tuple(self.recordset.import_type_id.available_importers()),
        )

    def test_get_set_raw_report(self):
        val = {"baz": "bar"}
        # store report
        self.recordset.set_report(val)
        # retrieve it, should be the same
        self.assertEqual(self.recordset.get_report(), val)
        new_val = {"foo": "boo"}
        # set a new value
        self.recordset.set_report(new_val)
        merged = val.copy()
        merged.update(new_val)
        # by default previous value is preserved and merged w/ the new one
        self.assertDictEqual(self.recordset.get_report(), merged)
        # unless we use `reset`
        val = {"goo": "gle"}
        # store report
        self.recordset.set_report(val, reset=True)
        self.assertDictEqual(self.recordset.get_report(), val)

    def test_get_report_html_data(self):
        val = {
            "_last_start": "2018-01-20",
            "res.partner": {
                "errored": list(range(10)),
                "skipped": list(range(4)),
                "updated": list(range(20)),
                "created": list(range(2)),
            },
        }
        self.recordset.set_report(val)
        data = self.recordset._get_report_html_data()
        self.assertEqual(data["recordset"], self.recordset)
        self.assertEqual(data["last_start"], "2018-01-20")
        by_model = data["report_by_model"]
        key = list(by_model.keys())[0]
        self.assertEqual(key._name, "ir.model")
        self.assertEqual(key.model, "res.partner")
