# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_importer.utils.mapper_utils import xmlid_to_rel

from ..utils import sanitize_external_id


class ProductProductRecordImporter(Component):
    _name = "product.product.importer"
    _inherit = ["common.product.importer"]
    _apply_on = "product.product"
    odoo_unique_key = "id"
    odoo_unique_key_is_xmlid = True

    def prepare_line(self, line):
        res = super().prepare_line(line)
        res["id"] = sanitize_external_id(line["id"])
        res["template_default_code"] = sanitize_external_id(
            line["template_default_code"]
        )
        res["categ_id"] = sanitize_external_id(line["categ_id"])
        return res


class ProductProductRecordHandler(Component):
    """Interact w/ odoo importable records."""

    _name = "product.product.handler"
    _inherit = "importer.odoorecord.handler"
    _apply_on = "product.product"

    def odoo_post_create(self, odoo_record, values, orig_values):
        self._set_external_id_on_template(odoo_record, values, orig_values)
        self._update_template_attributes(odoo_record, values, orig_values)

    def odoo_post_write(self, odoo_record, values, orig_values):
        self._update_template_attributes(odoo_record, values, orig_values)

    def _set_external_id_on_template(self, odoo_record, values, orig_values):
        """Set the External ID on the template once the variant created."""
        template = odoo_record.product_tmpl_id
        external_id = template.get_external_id()[template.id]
        if not external_id and orig_values["template_default_code"]:
            external_id = sanitize_external_id(orig_values["template_default_code"])
            module, id_ = external_id.split(".", 1)
            self.env["ir.model.data"].create(
                {
                    "name": id_,
                    "module": module,
                    "model": template._name,
                    "res_id": template.id,
                    "noupdate": False,
                }
            )

    def _update_template_attributes(self, odoo_record, values, orig_values):
        """Update the 'attribute_line_ids' field of the related template.

        We don't update this field directly to not trigger the 'write()' method
        of template (which triggers '_create_variant_ids()' in turn). Instead we
        fill the attributes + values by creating:

        - the corresponding 'product.template.attribute.line' on the template
          (product_template.attribute_line_ids) to reflect the state of the variant,
        - 'product.template.attribute.value' records making the link between a
          template attribute line and an attribute value, and link it to the
          variant through the M2M field 'product_template_attribute_value_ids'.
        """
        TplAttrLine = self.env["product.template.attribute.line"]
        TplAttrValue = self.env["product.template.attribute.value"]
        template = odoo_record.product_tmpl_id
        attr_columns = filter(
            lambda col: col.startswith("product_attr"), orig_values.keys()
        )
        tpl_attr_values = self.env["product.template.attribute.value"]
        # Detect and gather attributes and attribute values to import
        attr_values_to_import_ids = []
        for attr_column in attr_columns:
            if not orig_values[attr_column]:
                continue
            attr_value_external_id = sanitize_external_id(orig_values[attr_column])
            attr_value = self.env.ref(attr_value_external_id)
            # attr_values_to_import |= attr_value
            attr_values_to_import_ids.append(attr_value.id)
        # Detect if the set of attributes among this template is wrong
        # (if a previously variant V1 has been imported with attributes A
        # and B, we cannot import a second variant V2 with attributes A and C
        # for instance, attributes have to be the same among all variants of a
        # template)
        attr_values_to_import = self.env["product.attribute.value"].browse(
            attr_values_to_import_ids
        )
        attrs_to_import = attr_values_to_import.mapped("attribute_id")
        existing_variant = self.env["product.product"].search(
            [
                ("id", "!=", odoo_record.id),
                ("product_tmpl_id", "=", odoo_record.product_tmpl_id.id),
            ],
            limit=1,
        )
        existing_attrs = existing_variant.mapped(
            "product_template_attribute_value_ids.attribute_id"
        )
        if existing_variant and attrs_to_import != existing_attrs:
            raise ValueError(
                _(
                    "Product '{}' has not the same attributes than '{}'. "
                    "Unable to import it."
                ).format(odoo_record.default_code, existing_variant.default_code)
            )
        # Prepare attributes and attribute values
        for attr_value in attr_values_to_import:
            # Find the corresponding attribute line on the template
            # or create it if none is found
            attr = attr_value.attribute_id
            tpl_attr_line = template.attribute_line_ids.filtered(
                lambda l: l.attribute_id == attr
            )
            if not tpl_attr_line:
                tpl_attr_line = TplAttrLine.create(
                    {
                        "product_tmpl_id": template.id,
                        "attribute_id": attr.id,
                        "value_ids": [(6, False, [attr_value.id])],
                    }
                )
            # Ensure that the value exists in this attribute line.
            # The context key 'update_product_template_attribute_values' avoids
            # to create/unlink variants when values are updated on the template
            # attribute line.
            tpl_attr_line.with_context(
                update_product_template_attribute_values=False
            ).write({"value_ids": [(4, attr_value.id)]})
            # Get (and create if needed) the 'product.template.attribute.value'
            tpl_attr_value = TplAttrValue.search(
                [
                    ("attribute_line_id", "=", tpl_attr_line.id),
                    ("product_attribute_value_id", "=", attr_value.id),
                ]
            )
            if not tpl_attr_value:
                tpl_attr_value = TplAttrValue.create(
                    {
                        "attribute_line_id": tpl_attr_line.id,
                        "product_attribute_value_id": attr_value.id,
                    }
                )
            tpl_attr_values |= tpl_attr_value
        # Detect variant duplicates (same attributes)
        combination_indices = tpl_attr_values._ids2str()
        existing_product = self.env["product.product"].search(
            [
                ("id", "!=", odoo_record.id),
                ("product_tmpl_id", "=", odoo_record.product_tmpl_id.id),
                ("combination_indices", "=", combination_indices),
            ],
            limit=1,
        )
        if combination_indices and existing_product:
            raise ValueError(
                _(
                    "Product '{}' seems to be a duplicate of '{}' (same attributes). "
                    "Unable to import it."
                ).format(odoo_record.default_code, existing_product.default_code)
            )
        # It is required to set the whole template attribute values at the end
        # (and not in the loop) to not trigger internal mechanisms done by Odoo
        else:
            odoo_record.product_template_attribute_value_ids = tpl_attr_values


class ProductProductMapper(Component):
    _name = "product.product.mapper"
    _inherit = "importer.base.mapper"
    _apply_on = "product.product"

    direct = [
        # "id" needs to be in the mapped values to be converted as XML-ID
        # TODO: need to allow the use of fake destination fields like '_xmlid'
        # in direct mapping here:
        # https://github.com/OCA/connector/blob/13.0/connector/components/mapper.py#L891
        ("id", "id"),
        ("name", "name"),
        ("default_code", "default_code"),
        ("barcode", "barcode"),
        ("list_price", "list_price"),
        ("standard_price", "standard_price"),
        ("type", "type"),
        (xmlid_to_rel("uom_id"), "uom_id"),
        (xmlid_to_rel("categ_id"), "categ_id"),
    ]
    required = {"categ_id": "categ_id"}
    translatable = ["name"]

    @mapping
    def product_tmpl_id(self, record):
        if record.get("template_default_code"):
            template = self.env.ref(
                record["template_default_code"], raise_if_not_found=False
            )
            # If no product.template is found, it'll be created automatically
            # as usual when the product.product is created.Then the importer
            # will set its External ID.
            if template:
                return {"product_tmpl_id": template.id}
        return {}
