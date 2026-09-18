# Copyright ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class RecordSetImporter(Component):
    """Importer for recordsets."""

    _inherit = "importer.recordset"

    def create_and_run(self, chunk, recordset):
        # If stream, as soon as a chunk is ready, run the import of records
        if recordset.source_ref_id.stream:
            return self._create_and_run(chunk, recordset, new_cr=True)
        return super().create_and_run(chunk, recordset)
