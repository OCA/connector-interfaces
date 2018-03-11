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
                search_value = [model_mapping[x][search_field]
                                for x in search_value
                                if model_mapping.get(x)]
            if search_value:
                record[source_field] = search_value
                converter = backend_to_rel(
                    source_field,
                    search_field=search_field,
                )
                values[dest_field] = converter(self, record, dest_field)
        return values
