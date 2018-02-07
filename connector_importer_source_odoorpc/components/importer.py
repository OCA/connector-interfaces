# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class OdooRPCRecordImporter(Component):
    """Importer for records coming via OdooRPC source."""

    _name = 'odoorpc.base.importer'
    _inherit = 'importer.record'

    def _record_lines(self):
        """Yield only lines for current model.

        OdooRPC source can load different models at once
        if you `follow` relation fields.
        Here we make sure to work only on records that we expect.
        """
        lines = super()._record_lines()
        for line in lines:
            if self._apply_on and '_model' in line:
                if line['_model'] == self._apply_on:
                    yield line
            else:
                yield line
