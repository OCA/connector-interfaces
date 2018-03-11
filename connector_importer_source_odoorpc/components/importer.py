# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component
from collections import defaultdict


class OdooRPCRecordImporter(Component):
    """Importer for records coming via OdooRPC source."""

    _name = 'odoorpc.base.importer'
    _inherit = 'importer.record'

    def _record_lines(self):
        """Yield only lines for current model and set shared storage.

        OdooRPC source can load different models at once
        if you `follow` relation fields.
        Here we make sure to work only on records that we expect.
        Also, we might have followed fields that need to be stored
        in shared storage to be retrieved by mappers for fast conversion.
        """
        lines = self.record.get_data()
        # collect followed mapping
        followed_mapping = defaultdict(dict)
        for line in lines:
            if line.get('_followed_from'):
                followed_mapping[line['_model']][line['_line_nr']] = line
        # set it on shared store
        self.recordset.set_shared({'followed_mapping': followed_mapping})
        # now yield lines
        for line in lines:
            if self._apply_on and '_model' in line:
                if line['_model'] == self._apply_on:
                    yield line
            else:
                yield line

    def _load_mapper_options(self):
        opts = super()._load_mapper_options()
        opts.update({
            'followed_mapping':
                self.recordset.get_shared().get('followed_mapping', {}),
        })
        return opts
