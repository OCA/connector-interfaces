# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_importer.utils.mapper_utils import (
    backend_to_rel,
)


class OdooRPCBaseMapper(Component):
    _name = 'odoorpc.base.mapper'
    _inherit = 'importer.base.mapper'

    followed = [
        # source model, source field, search field, dest field
        # ('res.partner.category', 'category_id', 'name', 'profession_ids', ),
        # ('res.users', 'user_ids', 'login', 'user_ids', ),
    ]

    def _merge_relations(self, old_vals, new_vals):
        """Merges old and new values.

        If we have several source fields pointing to the same destination field
        we want to merge them. From backend_to_rel we will get [(6, 0, ids)]
        format, so this only merges ids together from old and new values."""
        new_vals[0][2].extend(old_vals[0][2])
        return new_vals

    @mapping
    def resolve_relations(self, record):
        values = {}
        followed_mapping = self.options.get('followed_mapping', {})
        for source_model, source_field, search_field, dest_field in self.followed:  # noqa
            model_mapping = followed_mapping.get(source_model, {})
            search_value = record[source_field]
            if isinstance(search_value, (list, tuple)):
                # [{'id': 215, '_followed_from': 'user_ids',
                #   'login': 'john.doe@foo.com',
                #   '_line_nr': 215, '_model': 'res.users'}

                # convert value to string here as dict keys in model_mapping
                # are strings. Because of the serialized field and json.loads
                ftype = self.model._fields[dest_field].type
                if ftype == 'many2one':
                    # man2one comes in the standard odoo format `(1, name)`
                    search_value = model_mapping[
                        str(search_value[0])
                    ][search_field]
                else:
                    search_value = [model_mapping[str(x)][search_field]
                                    for x in search_value
                                    if model_mapping.get(str(x))]
            if search_value:
                record[source_field] = search_value
                converter = backend_to_rel(
                    source_field,
                    search_field=search_field,
                )
                converted_vals = converter(self, record, dest_field)
                if (dest_field in values and
                        self.model._fields[dest_field].type.endswith('2many')):
                    converted_vals = self._merge_relations(
                        values.get(dest_field),
                        converted_vals
                    )
                values[dest_field] = converted_vals
        return values
