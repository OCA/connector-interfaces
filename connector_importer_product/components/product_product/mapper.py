# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.connector_importer.utils.mapper_utils import backend_to_rel


def _get_extra_fields(rel_model, record, prefix):
    extra_fields = []
    for k in record.keys():
        if not k.startswith(prefix):
            continue
        real_fname = k[len(prefix) :]
        if real_fname in rel_model._fields:
            extra_fields.append(real_fname)
    return extra_fields


def _get_or_create_supplier_partner_id(env, name):
    model = env["res.partner"]
    partner = model.search([("name", "=", name)], limit=1)
    if not partner:
        partner = partner.create({"name": name})
    return partner.id


def missing_supplier_handler(self, rel_model, record):
    """Handle create of missing supplier.

    `supplier` key/col will be used for the name.
    Any additional product.supplierinfo field can be passed
    by using its real name prefixed by `supplier_`.
    Eg: `supplier_product_name`, `supplier_product_code`, etc.
    """

    values = {
        "name": _get_or_create_supplier_partner_id(rel_model.env, record["supplier"]),
    }
    # TODO: we could generalize this approach and always look for all keys
    # startign with key + "." then we can apply the same conversion
    # as for `dynamic_fields` by field type on the related record.
    prefix = "supplier."
    extra_fields = _get_extra_fields(rel_model, record, prefix)
    for k in extra_fields:
        if record.get(k) is not None:
            values[k] = record[k]
    # TODO: we should rely on the supplier info importer for this job
    # but we should be able to configure the prefix in the options.
    return rel_model.create(values)


class ProductProductMapper(Component):
    _name = "product.product.mapper"
    # Non mapped fields will be managed by the dynamic mapper
    _inherit = "importer.mapper.dynamic"
    _apply_on = "product.product"
    _mapper_usage = "importer.mapper"

    direct = [
        (
            backend_to_rel(
                "supplier",
                search_field="name.name",
                create_missing=True,
                create_missing_handler=missing_supplier_handler,
            ),
            "seller_ids",
        ),
    ]
    required = {
        "default_code": "default_code",
        "name": "name",
    }
    translatable = ["name"]

    # def finalize(self, map_record, values):
    #     return values
