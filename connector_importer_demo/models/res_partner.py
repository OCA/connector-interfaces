# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class PartnerRecordHandler(Component):
    _name = "importer.odoorecord.handler.partner"
    _inherit = "importer.odoorecord.handler.csv.std"
    _apply_on = "res.partner"


class PartnerMapper(Component):
    _name = 'demo.partner.mapper'
    _inherit = 'importer.base.mapper.csv.std'
    _apply_on = 'res.partner'


class PartnerRecordImporter(Component):
    _name = 'demo.partner.importer'
    _inherit = 'importer.record.csv.std'
    _apply_on = 'res.partner'
