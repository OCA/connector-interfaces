# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class FakeSourceConsumer(models.Model):

    _name = "fake.source.consumer"
    _description = _name
    _inherit = "import.source.consumer.mixin"
    _description = "Fake source consumer"

    name = fields.Char()


class FakeSourceStatic(models.Model):

    _name = "fake.source.static"
    _description = _name
    _inherit = "import.source"
    _source_type = "static"
    _description = "Fake static source"

    fake_param = fields.Char()

    @property
    def _config_summary_fields(self):
        return super()._config_summary_fields + ["fake_param"]

    def _get_lines(self):
        for i in range(1, 21):
            yield {
                "id": i,
                "fullname": "Fake line #{}".format(i),
                "address": "Some fake place, {}".format(i),
            }

    def _sort_lines(self, lines):
        return reversed(list(lines))
