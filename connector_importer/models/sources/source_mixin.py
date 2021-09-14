# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from ...utils.import_utils import gen_chunks


class ImportSource(models.AbstractModel):
    """Define a source for an import.

    A source model is responsible for:

    * storing specific settings (chunk size, source params, etc)
    * retrieve source lines (connect to an external service, or db or read CSV)
    * yield lines in chunks
    * display configuration summary on the recordset (via config summary)
    * optionally, provide a reporter to create an extensive report for users.
    """

    _name = "import.source"
    _description = "Import source"
    _source_type = "none"
    _reporter_model = ""

    name = fields.Char(compute="_compute_name")
    chunk_size = fields.Integer(required=True, default=500, string="Chunks Size")
    config_summary = fields.Html(compute="_compute_config_summary")

    # tmpl that renders configuration summary
    _config_summary_template = "connector_importer.source_config_summary"

    def _compute_name(self):
        self.name = self._source_type

    @property
    def _config_summary_fields(self):
        """Fields automatically included in the summary.

        Override it to add your custom fields automatically to the summary.
        """
        return ["chunk_size"]

    @api.depends()
    def _compute_config_summary(self):
        """Generate configuration summary HTML.

        Configurations parameters can vary depending on the kind of source.
        To display meaningful information on the recordset
        w/out hacking the recordset view each time
        we generate a short HTML summary.

        For instance, if you are connecting to an external db
        you might want to show DSN, if you are loading a CSV
        you might want to show delimiter, quotechar and so on.

        To add your fields automatically to the summary,
        just override `_config_summary_fields`.
        They'll be automatically included in the summary.
        """
        template = self.env.ref(self._config_summary_template)
        for item in self:
            item.config_summary = template._render(item._config_summary_data())

    def _config_summary_data(self):
        """Collect data for summary."""
        return {
            "source": self,
            "summary_fields": self._config_summary_fields,
            "fields_info": self.fields_get(self._config_summary_fields),
        }

    @api.model
    def create(self, vals):
        """Override to update reference to source on the consumer."""
        res = super().create(vals)
        if self.env.context.get("active_model"):
            # update reference on consumer
            self.env[self.env.context["active_model"]].browse(
                self.env.context["active_id"]
            ).source_id = res.id
        return res

    def get_lines(self):
        """Retrieve lines to import."""
        self.ensure_one()
        # retrieve lines
        lines = self._get_lines()

        # sort them
        lines_sorted = self._sort_lines(lines)

        # no chunk size means no chunk of lines
        if not self.chunk_size:
            yield list(lines)
        for _i, chunk in enumerate(gen_chunks(lines_sorted, chunksize=self.chunk_size)):
            # get out of chunk iterator
            yield list(chunk)

    def _get_lines(self):
        """Your duty here..."""
        raise NotImplementedError()

    def _sort_lines(self, lines):
        """Override to customize sorting."""
        return lines

    def get_config_view_id(self):
        """Retrieve configuration view."""
        return (
            self.env["ir.ui.view"]
            .search([("model", "=", self._name), ("type", "=", "form")], limit=1)
            .id
        )

    def get_reporter(self):
        """Retrieve a specific reporter for this source.

        A report can be used to produce and extensive report for the end user.
        See `reporter` models.
        """
        return self.env.get(self._reporter_model)
