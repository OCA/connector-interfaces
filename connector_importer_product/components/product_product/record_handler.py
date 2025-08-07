# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import re
import unicodedata

from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector_importer.log import logger
from odoo.addons.connector_importer.utils.misc import sanitize_external_id


def slugify_one(s, max_length=0):
    # similar to odoo.addons.http_routing.models.ir_http.slugify_one
    # but no lower and no ext lib
    uni = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    slug_str = re.sub(r"[\W_]", " ", uni).strip()
    slug_str = re.sub(r"[-\s]+", "-", slug_str)
    return slug_str[:max_length] if max_length > 0 else slug_str


class ProductProductRecordHandler(Component):
    """Interact w/ odoo importable records."""

    _name = "product.product.handler"
    _inherit = "importer.odoorecord.handler"
    _apply_on = "product.product"

    def odoo_post_create(self, odoo_record, values, orig_values):
        self._update_template_attributes(odoo_record, values, orig_values)

    def odoo_post_write(self, odoo_record, values, orig_values):
        self._update_template_attributes(odoo_record, values, orig_values)

    def odoo_create(self, values, orig_values):
        odoo_record = super().odoo_create(values, orig_values)
        # Set the external ID for the template if necessary
        # TODO: add tests
        self._handle_template_xid(odoo_record, values, orig_values)
        return odoo_record

    def _handle_template_xid(self, odoo_record, values, orig_values):
        """Create the xid for the template if needed.

        The xid for the variant has been already created by `odoo_create`.
        If the template is identified via xid using the column `xid::product_tmpl_id`
        we must create this reference or other variant lines won't use the same template.
        """
        if self.must_generate_xmlid and orig_values.get("xid::product_tmpl_id"):
            tmpl_xid = sanitize_external_id(orig_values.get("xid::product_tmpl_id"))
            if not self.env.ref(tmpl_xid, raise_if_not_found=False):
                module, id_ = tmpl_xid.split(".", 1)
                self.env["ir.model.data"].create(
                    {
                        "name": id_,
                        "module": module,
                        "model": odoo_record.product_tmpl_id._name,
                        "res_id": odoo_record.product_tmpl_id.id,
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

        Assumptions:

        * `product.attribute` and `.value` must be imported beforehand
          using `product.attribute.importer` and `product.attribute.value.importer`
          respectively. Those importers will take care of prefixing the value
          found in `id` w/ the `__setup__.` module name to generate a valid xid.
          This will be later used to find the matching attribute here.

        * product attribute columns must contain the `product_attr` prefix
          and it should represent the XID of the `product.attribute` to match.

        * product attribute column values will be used to find the values
          which were already imported first by name then by XID.
          See `_find_or_create_attr_value` docs.
        """
        TplAttrLine = self.env["product.template.attribute.line"]
        TplAttrValue = self.env["product.template.attribute.value"]
        template = odoo_record.product_tmpl_id
        blacklist = self.work.options.mapper.get("source_key_blacklist", [])
        attr_columns = filter(
            lambda col: col.startswith("product_attr") and col not in blacklist,
            orig_values.keys(),
        )
        tpl_attr_values = self.env["product.template.attribute.value"]
        # Detect and gather attributes and attribute values to import
        attr_values_to_import_ids = []
        for attr_column in attr_columns:
            if not orig_values[attr_column]:
                continue
            attr = self._find_attr(attr_column, orig_values)
            attr_value = self._find_or_create_attr_value(attr, attr_column, orig_values)
            if attr_value:
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
                    "Product '%(code)s' has not the same attributes "
                    "than '%(existing_code)s'. "
                    "Unable to import it.",
                    code=odoo_record.default_code,
                    existing_code=existing_variant.default_code,
                )
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
        valid_tpl_attr_values = tpl_attr_values._without_no_variant_attributes()
        combination_indices = valid_tpl_attr_values._ids2str()
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
                    "Product '%(code)s' "
                    "seems to be a duplicate of '%(existing_code)s' (same attributes). "
                    "Unable to import it.",
                    code=odoo_record.default_code,
                    existing_code=existing_variant.default_code,
                )
            )
        # It is required to set the whole template attribute values at the end
        # (and not in the loop) to not trigger internal mechanisms done by Odoo
        else:
            odoo_record.product_template_attribute_value_ids = valid_tpl_attr_values

    def _find_attr(self, attr_column, orig_values):
        """Find matching attribute."""
        attr_xid = sanitize_external_id(attr_column)
        return self.env.ref(attr_xid)

    # TODO: add unit test
    def _find_or_create_attr_value(self, attr, attr_column, orig_values):
        """Find matching attribute value.

        The column name is used to compute the product.attribute xid. Eg:

            * product_attr_Size -> __setup__.product_attr_Size
            * product_attr_Color -> __setup__.product_attr_Color

        The value will be used to determine the product.attribute.value.
        The lookup happens in this order:

        1. search by name
        2. search by xid, assuming the value itself is already an xid.
        3. search by composed xid, assuming the value is the last part of an xid.
           The first part is computed as: `__setup__.$product_attr_xid_value_$col_value`.
           For instance, a column `product_attr_Size` could have the values
           "S" , "M", "L" and they will be converted
           to find their matching attributes, like this:

             * S -> product_attr_Size_value_S
             * M -> product_attr_Size_value_M
             * L -> product_attr_Size_value_L

        If no attribute value matching this convention is found,
        the value will be skipped unless `create_attribute_value_if_missing`
        flag is passed to `record_handler` options. Eg:

            - model: product.product
              options:
                importer:
                  odoo_unique_key: barcode
                mapper:
                  name: product.product.mapper
                record_handler:
                  create_attribute_value_if_missing: true
        """
        # 1st search by name
        orig_val = orig_values[attr_column]
        model = self.env["product.attribute.value"]
        attr_value = model.search(
            [("attribute_id", "=", attr.id), ("name", "=", orig_val)], limit=1
        )
        if not attr_value:
            # 2nd assume it's an xmlid
            attr_value = self.env.ref(sanitize_external_id(orig_val), False)
        if not attr_value and "_value_" not in orig_val:
            # 3rd try w/ auto generated xid
            attr_value_xid = self._make_attribute_value_xid(attr_column, orig_val)
            attr_value = self.env.ref(attr_value_xid, False)
        if not attr_value and self.create_attribute_value_if_missing:
            attr_value = self._create_missing_attribute_value(
                attr, attr_column, orig_val
            )
        if not attr_value:
            logger.error("Cannot determine product attr value: %s", orig_val)
        return attr_value

    def _make_attribute_value_xid(self, attr_column, orig_val):
        value = slugify_one(orig_val).replace("-", "_")
        xid = f"{attr_column}_value_{value}"
        return sanitize_external_id(xid)

    def _create_missing_attribute_value(self, attr, attr_column, orig_val):
        rec = self.env["product.attribute.value"].create(
            self._create_missing_attribute_value_values(attr, orig_val)
        )
        xid = self._make_attribute_value_xid(attr_column, orig_val)
        module, id_ = xid.split(".", 1)
        self.env["ir.model.data"].create(
            {
                "name": id_,
                "module": module,
                "model": rec._name,
                "res_id": rec.id,
                "noupdate": False,
            }
        )
        logger.info("Created product.attribute.value: %s", xid)
        return rec

    def _create_missing_attribute_value_values(self, attr, orig_val):
        return {"attribute_id": attr.id, "name": orig_val}

    @property
    def create_attribute_value_if_missing(self):
        return self.work.options.record_handler.get(
            "create_attribute_value_if_missing", False
        )
