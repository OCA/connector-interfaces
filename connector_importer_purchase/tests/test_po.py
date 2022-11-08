# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.tests.common import RecordCapturer
from odoo.tools import mute_logger

# TODO: move to c_importer
from .common import TestImportProductBase


class TestPurchase(TestImportProductBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_model = cls.env["res.partner"]
        cls.prod_model = cls.env["product.product"]
        for i in range(1, 7):
            rec = cls.prod_model.create(
                {
                    "name": f"Prod {i}",
                    "default_code": f"prod{i}",
                    "standard_price": 10.0 * i,
                }
            )
            setattr(cls, f"prod{i}", rec)

        for i in range(1, 4):
            rec = cls.partner_model.create(
                {
                    "name": f"Suppl {i}",
                }
            )
            setattr(cls, f"suppl{i}", rec)

        cls.importer_load_file(
            "connector_importer_purchase.demo_import_source_csv_purchase_order",
            "purchase_order.csv",
        )
        cls.recordset = cls.env.ref(
            "connector_importer_purchase.demo_import_recordset_purchase_order"
        )

    @mute_logger("[importer]")
    def test_po(self):
        records = []
        with RecordCapturer(self.env["purchase.order.line"].sudo(), []) as capt:
            self.recordset.run_import()
            records = capt.records

        self.assertEqual(len(records), 10)
        order1, order2, order3 = records.mapped("order_id").sorted("partner_ref")

        self.assertRecordValues(
            order1 + order2 + order3,
            [
                {
                    "partner_ref": "REF#1",
                    "partner_id": self.suppl1.id,
                },
                {
                    "partner_ref": "REF#2",
                    "partner_id": self.suppl2.id,
                },
                {
                    "partner_ref": "REF#3",
                    "partner_id": self.suppl3.id,
                },
            ],
        )
        self.assertRecordValues(
            order1.order_line.sorted("product_id"),
            [
                {
                    "name": "custom desc",
                    "product_id": self.prod1.id,
                    "product_qty": 4.0,
                    "price_unit": 10,
                },
                {
                    "name": self.prod2.display_name,
                    "product_id": self.prod2.id,
                    "product_qty": 5.0,
                    "price_unit": 20,
                },
                {
                    "name": self.prod3.display_name,
                    "product_id": self.prod3.id,
                    "product_qty": 6.0,
                    "price_unit": 30,
                },
                {
                    "name": self.prod4.display_name,
                    "product_id": self.prod4.id,
                    "product_qty": 10.0,
                    "price_unit": self.prod4.standard_price,
                },
            ],
        )
        self.assertRecordValues(
            order2.order_line.sorted("product_id"),
            [
                {
                    "name": "custom desc",
                    "product_id": self.prod1.id,
                    "product_qty": 4.0,
                    "price_unit": 10,
                },
                {
                    "name": self.prod2.display_name,
                    "product_id": self.prod2.id,
                    "product_qty": 5.0,
                    "price_unit": 20,
                },
            ],
        )
        self.assertRecordValues(
            order3.order_line.sorted("product_id"),
            [
                {
                    "name": self.prod3.display_name,
                    "product_id": self.prod3.id,
                    "product_qty": 6.0,
                    "price_unit": 40,
                },
                {
                    "name": self.prod4.display_name,
                    "product_id": self.prod4.id,
                    "product_qty": 6.0,
                    "price_unit": self.prod4.standard_price,
                },
                {
                    "name": self.prod5.display_name,
                    "product_id": self.prod5.id,
                    "product_qty": 6.0,
                    "price_unit": 15,
                },
                {
                    "name": self.prod6.display_name,
                    "product_id": self.prod6.id,
                    "product_qty": 1.0,
                    "price_unit": self.prod6.standard_price,
                },
            ],
        )
