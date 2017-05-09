# -*- coding: utf-8 -*-
# Author: Simone Orsi
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, tools

from ..utils.importer_utils import gen_chunks, CSVReader, guess_csv_metadata


class ImportSourceConsumerdMixin(models.AbstractModel):
    _name = 'import.source.consumer.mixin'
    _description = 'Import source consumer'

    source_id = fields.Integer(
        string='Source ID',
        required=False,
        ondelete='cascade',
    )
    source_model = fields.Selection(
        string='Source type',
        selection='_selection_source_ref_id',
    )
    source_ref_id = fields.Reference(
        string='Source',
        compute='_compute_source_ref_id',
        selection='_selection_source_ref_id',
        store=True,
    )
    source_config_summary = fields.Html(
        compute='_compute_source_config_summary',
        readonly=True,
    )

    @api.multi
    @api.depends('source_model', 'source_id')
    def _compute_source_ref_id(self):
        for item in self:
            if not item.source_id or not item.source_model:
                continue
            item.source_ref_id = '{0.source_model},{0.source_id}'.format(item)

    @api.model
    @tools.ormcache('self')
    def _selection_source_ref_id(self):
        domain = [('model', '=like', 'import.source.%')]
        return [(r.model, r.name)
                for r in self.env['ir.model'].search(domain)
                if not r.model.endswith('mixin')]

    @api.multi
    @api.depends('source_ref_id', )
    def _compute_source_config_summary(self):
        for item in self:
            if not item.source_ref_id:
                continue
            item.source_config_summary = item.source_ref_id.config_summary

    @api.multi
    def open_source_config(self):
        self.ensure_one()
        action = self.env[self.source_model].get_formview_action()
        action.update({
            'views': [
                (self.env[self.source_model].get_config_view_id(), 'form'),
            ],
            'res_id': self.source_id,
            'target': 'new',
        })
        return action

    def get_source(self):
        return self.source_ref_id


class ImportSource(models.AbstractModel):
    _name = 'import.source'
    _description = 'Import source'
    _source_type = 'none'
    _reporter_model = ''

    name = fields.Char(
        compute=lambda self: self._source_type,
        readony=True,
    )
    chunk_size = fields.Integer(
        required=True,
        default=500,
        string='Chunks Size'
    )
    config_summary = fields.Html(
        compute='_compute_config_summary',
        readonly=True,
    )

    _config_summary_template = 'connector_importer.source_config_summary'
    _config_summary_fields = ('chunk_size', )

    @api.depends()
    def _compute_config_summary(self):
        template = self.env.ref(self._config_summary_template)
        for item in self:
            item.config_summary = template.render(item._config_summary_data())

    def _config_summary_data(self):
        info = []
        for fname in self._config_summary_fields:
            info.append((fname, self[fname]))
        return {
            'source': self,
            'summary_fields': self._config_summary_fields,
            'fields_info': self.fields_get(self._config_summary_fields),
        }

    @api.model
    def create(self, vals):
        res = super(ImportSource, self).create(vals)
        if self.env.context.get('active_model'):
            # update reference on consumer
            self.env[self.env.context['active_model']].browse(
                self.env.context['active_id']).source_id = res.id
        return res

    @api.multi
    def get_lines(self):
        self.ensure_one()
        # retrieve lines
        lines = self._get_lines()

        # sort them
        lines_sorted = self._sort_lines(lines)

        for i, chunk in enumerate(gen_chunks(lines_sorted,
                                  chunksize=self.chunk_size)):
            # get out of chunk iterator
            yield list(chunk)

    def _get_lines(self):
        raise NotImplementedError()

    def _sort_lines(self, lines):
        return lines

    def get_config_view_id(self):
        return self.env['ir.ui.view'].search([
            ('model', '=', self._name),
            ('type', '=', 'form')], limit=1).id

    def get_reporter(self):
        return self.env.get(self._reporter_model)


class CSVSource(models.Model):
    _name = 'import.source.csv'
    _inherit = 'import.source'
    _description = 'CSV import source'
    _source_type = 'csv'
    _reporter_model = 'reporter.csv'

    csv_file = fields.Binary('CSV file')
    # use these to load file from an FS path
    csv_filename = fields.Char('CSV filename')
    csv_filesize = fields.Char(
        string='CSV filesize',
        compute='_compute_csv_filesize',
        readonly=True,
    )
    csv_path = fields.Char('CSV path')
    csv_delimiter = fields.Char(
        string='CSV delimiter',
        default=';',
    )
    csv_quotechar = fields.Char(
        string='CSV quotechar',
        default='"',
    )
    _config_summary_fields = ImportSource._config_summary_fields + (
        'csv_filename', 'csv_filesize', 'csv_delimiter', 'csv_quotechar',
    )

    @api.onchange('csv_file')
    def _onchance_csv_file(self):
        if self.csv_file:
            meta = guess_csv_metadata(self.csv_file.decode('base64'))
            if meta:
                self.csv_delimiter = meta['delimiter']
                self.csv_quotechar = meta['quotechar']

    def _filesize_human(self, size, suffix='B'):
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(size) < 1024.0:
                return "%3.1f%s%s" % (size, unit, suffix)
            size /= 1024.0
        return "%.1f%s%s" % (size, 'Y', suffix)

    @api.depends('csv_file')
    def _compute_csv_filesize(self):
        for item in self:
            if item.csv_file:
                item.csv_filesize = self._filesize_human(
                    len(item.csv_file.decode('base64')))

    def _get_lines(self):
        # read CSV
        reader_args = {
            'delimiter': self.csv_delimiter,
        }
        if self.csv_path:
            # TODO: join w/ filename
            reader_args['filepath'] = self.csv_path
        else:
            reader_args['filedata'] = self.csv_file

        reader = CSVReader(**reader_args)
        return reader.read_lines()

    # TODO: this stuff is now unrelated from backend version must be refactored
    # # handy fields to make the example attachment
    # # downloadable within recordset view
    # example_file_xmlid = fields.Char()
    # example_file_url = fields.Char(
    #     string='Download example file',
    #     compute='_compute_example_file_url',
    #     readonly=True,
    # )
    #
    # def _get_example_attachment(self):
    #     # You can define example file by creating attachments
    #     # with an xmlid matching the import type/key
    #     # `connector_importer.example_file_$version_key`
    #     if not self.backend_id.version or not self.import_type_id:
    #         return
    #     xmlid = self.example_file_xmlid
    #     if not xmlid:
    #         xmlid = u'connector_importer.examplefile_{}_{}'.format(
    #             self.backend_id.version.replace('.', '_'),
    #             self.import_type_id.key)
    #     return self.env.ref(xmlid, raise_if_not_found=0)
    #
    # @api.depends('backend_id.version', 'import_type_id', 'example_file_xmlid')
    # def _compute_example_file_url(self):
    #     att = self._get_example_attachment()
    #     if att:
    #         self.example_file_url = u'/web/content/{}/{}'.format(
    #             att.id, att.name)
