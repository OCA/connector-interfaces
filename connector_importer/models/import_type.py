# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models


class ImportType(models.Model):
    """Define an import.

    An import type describes what an recordset should do.
    You can describe an import using the `settings` field.
    Here you can declare what you want to import (model) and how (importer).

    Settings example:

        product.template::template.importer.component.name
        product.product::product.importer.component.name

    Each line contains a couple model::importer.
    The model is what you want to import, the importer states
    the name of the connector component to handle the import for that model.

    The importer machinery will run the imports for all the models declared
    and will retrieve their specific importerts to execute them.
    """

    _name = "import.type"
    _description = "Import type"

    name = fields.Char(required=True, help="A meaningful human-friendly name")
    key = fields.Char(required=True, help="Unique mnemonic identifier")
    settings = fields.Text(
        string="Settings",
        required=True,
        help="""
            # comment me
            product.template::template.importer.component.name
            product.product::product.importer.component.name
            # another one
            product.supplierinfo::supplierinfo.importer.component.name
        """,
    )
    use_job = fields.Boolean(
        string="Use job",
        help=(
            "For each importer used in the settings, one job will be spawned. "
            "Untick the box if an importer depends on the result of a "
            "previous one (for instance to link a record to the previously "
            "created one)."
        ),
        default=True,
    )
    _sql_constraints = [
        ("key_uniq", "unique (key)", _("Import type `key` must be unique!"))
    ]
    # TODO: provide default source and configuration policy
    # for an import type to ease bootstrapping recordsets from UI.
    # default_source_model_id = fields.Many2one()

    def available_models(self):
        """Retrieve available import models and their importers.

        Parse `settings` and yield a tuple
            `(model, importer, is_last_importer)`.
        """
        self.ensure_one()
        lines = self.settings.strip().splitlines()
        for _line in lines:
            line = _line.strip()
            if line and not line.startswith("#"):
                model_name, importer = line.split("::")
                is_last_importer = False
                if _line == lines[-1]:
                    is_last_importer = True
                yield (model_name.strip(), importer.strip(), is_last_importer)
