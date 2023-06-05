# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tools import DotDict

from .common import TestImportProductBase


class TestProduct(TestImportProductBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prod = cls.env["product.product"].create({"name": "Test prod"})
        cls.env["ir.model.data"].create(
            {
                "name": "variant_test_1",
                "module": "__setup__",
                "model": cls.prod._name,
                "res_id": cls.prod.id,
                "noupdate": False,
            }
        )
        cls.env["ir.model.data"].create(
            {
                "name": "tmpl_test_1",
                "module": "__setup__",
                "model": cls.prod.product_tmpl_id._name,
                "res_id": cls.prod.product_tmpl_id.id,
                "noupdate": False,
            }
        )
        cls.prod_attr = cls.env["product.attribute"].create({"name": "Size"})
        cls.prod_attr_imd = cls.env["ir.model.data"].create(
            {
                "name": "product_attr_Size",
                "module": "__setup__",
                "model": cls.prod_attr._name,
                "res_id": cls.prod_attr.id,
                "noupdate": False,
            }
        )
        cls.prod_attr_value_L = cls.env["product.attribute.value"].create(
            {"attribute_id": cls.prod_attr.id, "name": "L"}
        )
        cls.prod_attr_value_M = cls.env["product.attribute.value"].create(
            {
                "attribute_id": cls.prod_attr.id,
                "name": "M",
            }
        )
        # conventional xid
        cls.env["ir.model.data"].create(
            {
                "name": "product_attr_Size_value_M",
                "module": "__setup__",
                "model": cls.prod_attr_value_M._name,
                "res_id": cls.prod_attr_value_M.id,
                "noupdate": False,
            }
        )
        # custom xid
        cls.env["ir.model.data"].create(
            {
                "name": "product_attr_SizeM",
                "module": "__setup__",
                "model": cls.prod_attr_value_M._name,
                "res_id": cls.prod_attr_value_M.id,
                "noupdate": False,
            }
        )

    def _get_handler(self, options=None):
        options = options or {"importer": {}, "mapper": {}, "record_handler": {}}
        with self.backend.work_on(
            "import.record",
            options=DotDict(options),
        ) as work:
            return work.component_by_name(
                "product.product.handler", model_name="product.product"
            )

    def test_find_attr_not_found(self):
        self.prod_attr_imd.unlink()
        handler = self._get_handler()
        attr_column = "product_attr_Size"
        orig_values = {attr_column: "L"}
        with self.assertRaisesRegex(
            ValueError,
            "External ID not found in the system: __setup__.product_attr_Size",
        ):
            self.assertEqual(
                handler._find_attr(attr_column, orig_values).name, "TEST_1"
            )

    def test_find_attr_found(self):
        handler = self._get_handler()
        attr_column = "product_attr_Size"
        orig_values = {attr_column: "L"}
        self.assertEqual(handler._find_attr(attr_column, orig_values), self.prod_attr)

    def test_find_or_create_attr_value_by_name(self):
        handler = self._get_handler()
        attr_column = "product_attr_Size"
        orig_values = {attr_column: "L"}
        self.assertEqual(
            handler._find_or_create_attr_value(
                self.prod_attr, attr_column, orig_values
            ),
            self.prod_attr_value_L,
        )

    def test_find_or_create_attr_value_by_xid_conventional(self):
        handler = self._get_handler()
        attr_column = "product_attr_Size"
        # Value does not match name anymore, but it matched the conventional auto-computed xid
        orig_values = {attr_column: "M"}
        self.prod_attr_value_M.name = "Medium"
        self.assertEqual(
            handler._find_or_create_attr_value(
                self.prod_attr, attr_column, orig_values
            ),
            self.prod_attr_value_M,
        )

    def test_find_or_create_attr_value_by_xid_custom(self):
        handler = self._get_handler()
        attr_column = "product_attr_Size"
        # pass a specific value for xid
        orig_values = {attr_column: "product_attr_SizeM"}
        self.assertEqual(
            handler._find_or_create_attr_value(
                self.prod_attr, attr_column, orig_values
            ),
            self.prod_attr_value_M,
        )

    def test_find_or_create_attr_value_create_missing(self):
        handler = self._get_handler(
            options=dict(record_handler=dict(create_attribute_value_if_missing=True))
        )
        attr_column = "product_attr_Size"
        orig_values = {attr_column: "XL"}
        self.assertFalse(
            self.env.ref(
                "__setup__.product_attr_Size_value_XL", raise_if_not_found=False
            )
        )
        self.assertEqual(
            handler._find_or_create_attr_value(
                self.prod_attr, attr_column, orig_values
            ).name,
            "XL",
        )
        self.assertTrue(
            self.env.ref(
                "__setup__.product_attr_Size_value_XL", raise_if_not_found=False
            )
        )
