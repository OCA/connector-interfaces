# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class PartnerMapper(Component):
    _name = 'fake.partner.mapper'
    _inherit = 'importer.base.mapper'
    _apply_on = 'res.partner'

    required = {
        'fullname': 'name',
        'id': 'ref',
    }

    defaults = [
        ('is_company', False),
    ]

    direct = [
        ('id', 'ref'),
        ('fullname', 'name'),
    ]


class PartnerRecordImporter(Component):
    _name = 'fake.partner.importer'
    _inherit = 'importer.record'
    _apply_on = 'res.partner'

    odoo_unique_key = 'ref'

    def create_context(self):
        return {'tracking_disable': True}

    write_context = create_context
