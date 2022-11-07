# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, api, exceptions, fields, models
from odoo.tools import DotDict

_logger = logging.getLogger(__name__)


try:
    import yaml
except ImportError:
    _logger.debug("`yaml` lib is missing")


class ImportType(models.Model):
    """Define an import.

    An import type describes what an recordset should do.
    You can describe an import using the `options` field with YAML format.
    Here you can declare what you want to import (model) and how (importer).

    Options example:

    - model: product.template
      importer: template.importer.component.name
      context:
        key1: foo
      # will be ignored
      description: a nice import
      options:
        mapper:
          one: False
        tracking_handler:
          one: False

    - model: product.product
      importer: product.importer.component.name
      context:
        key1: foo
      # will be ignored
      description: a nice import
      options:
        importer:
          break_on_error: True
        mapper:
            name: my.nice.mapper
        record_handler:
          one: False

    The model is what you want to import, the importer states
    the name of the connector component to handle the import for that model.

    The importer machinery will run the imports for all the models declared
    and will retrieve their specific importerts to execute them.
    """

    _name = "import.type"
    _description = "Import type"

    name = fields.Char(required=True, help="A meaningful human-friendly name")
    description = fields.Text()
    key = fields.Char(required=True, help="Unique mnemonic identifier")
    options = fields.Text(help="YAML configuration")
    settings = fields.Text(
        string="Legacy Settings",
        required=False,
        help="""
            # comment me
            product.template::template.importer.component.name
            product.product::product.importer.component.name
            # another one
            product.supplierinfo::supplierinfo.importer.component.name
        """,
    )
    use_job = fields.Boolean(
        help=(
            "For each importer used in the settings, one job will be spawned. "
            "Untick the box if an importer depends on the result of a "
            "previous one (for instance to link a record to the previously "
            "created one)."
        ),
        default=True,
    )
    _sql_constraints = [
        ("key_uniq", "unique (key)", "Import type `key` must be unique!")
    ]
    # TODO: provide default source and configuration policy
    # for an import type to ease bootstrapping recordsets from UI.
    # default_source_model_id = fields.Many2one()

    @api.constrains("options")
    def _check_options(self):
        no_options = self.browse()
        for rec in self:
            if not rec.options and not rec.settings:
                no_options.append(rec)
            # TODO: validate yaml schema (maybe w/ Cerberus?)
        if no_options:
            raise exceptions.UserError(
                _("No options found for: {}.").format(
                    ", ".join(no_options.mapped("name"))
                )
            )

    def _load_options(self):
        return yaml.safe_load(self.options or "") or []

    def available_importers(self):
        self.ensure_one()
        if self.settings:
            for item in self._legacy_available_importers():
                yield item
        options = self._load_options()
        for line in options:
            is_last_importer = False
            if line == options[-1]:
                is_last_importer = True
            yield self._make_importer_info(line, is_last_importer=is_last_importer)

    def _make_importer_info(self, line, is_last_importer=True):
        """Prepare importer information.

        :param line: dictionary representing a config line from `settings`
        :param is_last_importer: boolean to state if the line represents the last one
        :return: odoo.tools.DotDict instance containing all importer options.
        """
        res = DotDict(line, is_last_importer=is_last_importer)
        for key in ("importer", "options", "context"):
            if key not in res:
                res[key] = self._importer_info_defaults.get(key, {})
        for k in ("importer", "mapper", "record_handler", "tracking_handler"):
            if k not in res.options:
                res["options"][k] = {}
        return res

    _importer_info_defaults = {
        "importer": {
            "name": "importer.record",
        },
    }

    # TODO: trash it for v14
    def _legacy_available_importers(self):
        for item in self.available_models():
            yield self._make_importer_info(
                {"model": item[0], "importer": item[1]}, is_last_importer=item[2]
            )

    def available_models(self):
        """Retrieve available import models and their importers.

        Parse `settings` and yield a tuple
            `(model, importer, is_last_importer)`.
        """
        _logger.warning("DEPRECATED legacy settings: move to JSON settings.")
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
