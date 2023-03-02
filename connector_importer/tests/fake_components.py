# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class PartnerMapper(Component):
    _name = "fake.partner.mapper"
    _inherit = "importer.base.mapper"
    _apply_on = "res.partner"

    required = {"fullname": "name", "id": "ref"}

    defaults = [("is_company", False)]

    direct = [("id", "ref"), ("fullname", "name")]

    def finalize(self, map_record, values):
        res = super().finalize(map_record, values)
        # allow easy simulation of broken import
        if self.env.context.get("_test_break_import"):
            raise ValueError(self.env.context.get("_test_break_import"))
        return res


class PartnerRecordImporter(Component):
    _name = "fake.partner.importer"
    _inherit = "importer.record"
    _apply_on = "res.partner"

    odoo_unique_key = "ref"

    def create_context(self):
        return {"tracking_disable": True}

    write_context = create_context


# Same component but with the "id" source column handled as an XML-ID


class PartnerMapperXMLID(Component):
    _name = "fake.partner.mapper.xmlid"
    _inherit = "importer.base.mapper"
    _apply_on = "res.partner"

    required = {"fullname": "name"}

    defaults = [("is_company", False)]

    direct = [("id", "id"), ("id", "ref"), ("fullname", "name")]


class PartnerRecordImporterXMLID(Component):
    _name = "fake.partner.importer.xmlid"
    _inherit = "importer.record"
    _apply_on = "res.partner"

    odoo_unique_key = "id"

    def create_context(self):
        return {"tracking_disable": True}

    def prepare_line(self, line):
        res = super().prepare_line(line)
        res["id"] = "__import__." + line["id"]
        return res

    write_context = create_context
