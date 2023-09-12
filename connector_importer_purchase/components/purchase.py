# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector_importer.utils.mapper_utils import backend_to_rel

suppplier_backend_to_rel = backend_to_rel(
    "supplier.name",
    search_field="name",
)


def create_missing_order(self, rel_model, record):
    supplier_id = suppplier_backend_to_rel(self, record, "partner_id")
    values = {
        "partner_ref": record["order_id.partner_ref"],
        "partner_id": supplier_id,
    }
    return rel_model.create(values)


class PurchaseOrderImportMapper(Component):
    _name = "purchase.order.import.mapper"
    # Non mapped fields will be managed by the dynamic mapper
    _inherit = "importer.mapper.dynamic"
    _apply_on = "purchase.order.line"

    direct = [
        (
            backend_to_rel(
                "order_id.partner_ref",
                search_field="partner_ref",
                create_missing=True,
                create_missing_handler=create_missing_order,
            ),
            "order_id",
        ),
        (
            suppplier_backend_to_rel,
            "partner_id",
        ),
        (
            backend_to_rel(
                "product_id",
                search_field="default_code",
            ),
            "product_id",
        ),
    ]

    required = {
        "order_id.partner_ref": "order_id",
        "supplier.name": "__",
        "product_id": "product_id",
    }


class PurchaseOrderImportRecordHandler(Component):
    _name = "purchase.order.line.import.handler"
    _inherit = "importer.odoorecord.handler"
    _apply_on = "purchase.order.line"

    # TODO: allow to define record_handler options
    # so that we can pass a mapping of
    # source_key/destination_key : domain_key to build a custom domain,
    # or allow to pass a full domain snippet to be interpolated.
    # This way we can get rid of record handlers for these simple cases.
    def odoo_find_domain(self, values, orig_values):
        domain = [
            (self.unique_key, "=", orig_values[self.unique_key]),
            ("product_id", "=", values["product_id"]),
        ]
        return domain
