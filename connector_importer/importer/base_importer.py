# -*- coding: utf-8 -*-
# Author: Simone Orsi
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.connector.unit.synchronizer import Importer
from odoo import fields

from ..backends import import_backend
from ..log import logger
from ..events import chunk_finished_event


@import_backend
class BaseImporter(Importer):
    _model_name = ''


@import_backend
class RecordSetImporter(BaseImporter):
    """Base importer for recordsets."""

    _model_name = 'import.recordset'

    def run(self, recordset, **kw):
        # update recordset report
        recordset.set_report({
            '_last_start': fields.Datetime.now(),
        }, reset=True)
        msg = 'START RECORDSET {0}({1})'.format(recordset.name,
                                                recordset.id)
        logger.info(msg)

        record_model = recordset.record_ids

        source = recordset.get_source()
        for chunk in source.get_lines():
            # create chuncked records and run their imports
            record = record_model.create({'recordset_id': recordset.id})
            # store data
            record.set_data(chunk)
            record.run_import()


class ChunkReport(dict):
    """A smarter dict for chunk data."""

    report_keys = (
        'created',
        'updated',
        'errored',
        'skipped',
    )

    def __init__(self, **kwargs):
        super(ChunkReport, self).__init__(**kwargs)
        for k in self.report_keys:
            self[k] = []

    def track_error(self, item):
        self['errored'].append(item)

    def track_skipped(self, item):
        self['skipped'].append(item)

    def track_updated(self, item):
        self['updated'].append(item)

    def track_created(self, item):
        self['created'].append(item)

    def counters(self):
        res = {}
        for k, v in self.iteritems():
            res[k] = len(v)
        return res


class OdooRecordMixin(object):

    _model_name = ''
    unique_key = ''

    def find_domain(self, values, orig_values):
        return [(self.unique_key, '=', values[self.unique_key])]

    def find(self, values, orig_values):
        """Find any existing item."""
        item = self.model.search(
            self.find_domain(values, orig_values),
            order='create_date desc', limit=1)
        return item

    def exists(self, values, orig_values):
        """Return true if the items exists."""
        return bool(self.find(values, orig_values))

    def default_values(self):
        """Values that are automatically assigned."""
        return self.mapper.default_values()

    def translatable_keys(self, create=False):
        """Keys that are translatable."""
        return self.mapper.translatable_keys()

    def translatable_langs(self):
        return self.env['res.lang'].search([
            ('translatable', '=', True)]).mapped('code')

    def make_translation_key(self, key, lang):
        return u'{}:{}'.format(key, lang)

    def collect_translatable(self, values, orig_values):
        """Get translations values for `mapper.translatable_keys`.

        We assume that the source contains extra columns in the form:

            `mapper_key:lang`

        whereas `mapper_key` is an odoo record field to translate
        and lang matches one of the installed languages.

        Translatable keys must be declared on the mapper
        within the attribute `translatable`.
        """
        translatable = {}
        if not self.translatable_keys():
            return translatable
        for lang in self.translatable_langs():
            for key in self.translatable_keys():
                # eg: name:fr_FR
                tkey = self.make_translation_key(key, lang)
                if tkey in orig_values and values.get(key):
                    if lang not in translatable:
                        translatable[lang] = {}
                    # we keep only translation for existing values
                    translatable[lang][key] = orig_values.get(tkey)
        return translatable

    def update_translations(self, odoo_record, translatable, ctx=None):
        ctx = ctx or {}
        for lang, values in translatable.iteritems():
            odoo_record.with_context(
                lang=lang, **self.write_context()).write(values)

    def pre_create(self, values, orig_values):
        """Do some extra stuff before creating a missing object."""
        pass

    def post_create(self, odoo_record, values, orig_values):
        """Do some extra stuff after creating a missing object."""
        pass

    def create_context(self):
        """Inject context variables on create."""
        return {}

    def create(self, values, orig_values):
        """Create a new odoo record."""
        self.pre_create(values, orig_values)
        # TODO: remove keys that are not model's fields
        odoo_record = self.model.with_context(
            **self.create_context()).create(values)
        self.post_create(odoo_record, values, orig_values)
        translatable = self.collect_translatable(values, orig_values)
        self.update_translations(odoo_record, translatable)
        return odoo_record

    def pre_write(self, odoo_record, values, orig_values):
        """Do some extra stuff before updating an existing object."""
        pass

    def post_write(self, odoo_record, values, orig_values):
        """Do some extra stuff after updating an existing object."""
        pass

    def write_context(self):
        """Inject context variables on write."""
        return {}

    def write(self, values, orig_values):
        """Update an existing odoo record."""
        # TODO: add a checkpoint? log something?
        odoo_record = self.find(values, orig_values)
        self.pre_write(odoo_record, values, orig_values)
        # TODO: remove keys that are not model's fields
        odoo_record.with_context(**self.write_context()).write(values)
        self.post_write(odoo_record, values, orig_values)
        translatable = self.collect_translatable(values, orig_values)
        self.update_translations(odoo_record, translatable)
        return odoo_record


class TrackingMixin(object):

    _model_name = ''
    _chunk_report = None

    @property
    def chunk_report(self):
        if not self._chunk_report:
            self._chunk_report = ChunkReport()
        return self._chunk_report

    def chunk_report_item(self, line, odoo_record=None, message=''):
        return {
            'line_nr': line['_line_nr'],
            'message': message,
            'model': self._model_name,
            'odoo_record': odoo_record.id if odoo_record else None,
        }

    def _log(self, msg, line=None, level='info'):
        handler = getattr(self._logger, level)
        msg = u'{prefix}{line}[model: {model}] {msg}'.format(
            prefix=self._log_prefix,
            line='[line: {}]'.format(line['_line_nr']) if line else '',
            model=self._model_name,
            msg=msg
        )
        handler(msg)

    def _log_updated(self, values, line, odoo_record, message=''):
        self._log('UPDATED [id: {}]'.format(odoo_record.id), line=line)
        self.chunk_report.track_updated(self.chunk_report_item(
            line, odoo_record=odoo_record, message=message
        ))

    def _log_error(self, values, line, odoo_record, message=''):
        if isinstance(message, Exception):
            message = str(message)
        self._log(message, line=line, level='error')
        self.chunk_report.track_error(self.chunk_report_item(
            line, odoo_record=odoo_record, message=message
        ))

    def _log_created(self, values, line, odoo_record, message=''):
        self._log('CREATED [id: {}]'.format(odoo_record.id), line=line)
        self.chunk_report.track_created(self.chunk_report_item(
            line, odoo_record=odoo_record, message=message
        ))

    def _log_skipped(self, values, line, skip_info):
        # `skip_it` could contain a msg
        self._log('SKIPPED ' + skip_info.get('message'),
                  line=line, level='warn')

        item = self.chunk_report_item(line)
        item.update(skip_info)
        self.chunk_report.track_skipped(item)

    def _prepare_report(self, previous):
        # init a new report
        report = ChunkReport()
        # merge previous and current
        for k, v in report.iteritems():
            prev = previous.get(self._model_name, {}).get(k, [])
            report[k] = prev + self.chunk_report[k]
        return report


@import_backend
class RecordImporter(BaseImporter, OdooRecordMixin, TrackingMixin):
    """Base importer for records."""

    # _base_mapper = ''
    _model_name = ''
    # log and report errors
    # do not make the whole import fail
    _break_on_error = False

    def required_keys(self, create=False):
        """Keys that are mandatory to import a line."""
        req = self.mapper.required_keys()
        all_values = []
        for k, v in req.iteritems():
            # make sure values are always tuples
            # as we support multiple dest keys
            if not isinstance(v, (tuple, list)):
                req[k] = (v, )
            all_values.extend(req[k])
        if (self.unique_key and
                self.unique_key not in req.keys() and
                self.unique_key not in all_values):
            # this one is REALLY required :)
            req[self.unique_key] = (self.unique_key, )
        return req

    def _check_missing(self, source_key, dest_key, values, orig_values):
        missing = (not source_key.startswith('__') and
                   orig_values.get(source_key) is None)
        if missing:
            msg = 'MISSING REQUIRED SOURCE KEY={}'.format(source_key)
            if self.unique_key and values.get(self.unique_key):
                msg += ': {}={}'.format(
                    self.unique_key, values[self.unique_key])
            return {
                'message': msg,
            }
        missing = (not dest_key.startswith('__') and
                   values.get(dest_key) is None)
        if missing:
            msg = 'MISSING REQUIRED DESTINATION KEY={}'.format(dest_key)
            if self.unique_key and values.get(self.unique_key):
                msg += ': {}={}'.format(
                    self.unique_key, values[self.unique_key])
            return {
                'message': msg,
            }
        return False

    def skip_it(self, values, orig_values):
        """Skip item import conditionally... if you want ;).

        You can return back `False` to not skip
        or a dictionary containing info about skip reason.
        """
        msg = ''
        required = self.required_keys()
        for source_key, dest_key in required.iteritems():
            # we support multiple destination keys
            for _dest_key in dest_key:
                missing = self._check_missing(
                    source_key, _dest_key, values, orig_values)
                if missing:
                    return missing

        if self.exists(values, orig_values) \
                and not self.recordset.override_existing:
            msg = 'ALREADY EXISTS'
            if self.unique_key:
                msg += ': {}={}'.format(
                    self.unique_key, values[self.unique_key])
            return {
                'message': msg,
                'odoo_record': self.find(values, orig_values).id,
            }
        return False

    def cleanup_line(self, line):
        """Apply basic cleanup on lines."""
        # we cannot alter dict keys while iterating
        res = {}
        for k, v in line.iteritems():
            if not k.startswith('_'):
                k = self.clean_line_key(k)
            if isinstance(v, basestring):
                v = v.strip()
            res[k] = v
        return res

    def clean_line_key(self, key):
        """Clean record key.

        Sometimes your CSV source do not have proper keys,
        they can contain a lot of crap or they can change
        lower/uppercase from import to import.
        You can override this method to normalize keys
        and make your import mappers work reliably.
        """
        return key.strip()

    def prepare_line(self, line):
        """Pre-manipulate a line if needed."""
        pass

    def _init(self, recordset):
        self.recordset = recordset
        self.backend = self.recordset.backend_id
        self._log_prefix = self.recordset.import_type_id.key + ' '
        self._logger = logger

    def _do_report(self):
        previous = self.recordset.get_report()
        report = self._prepare_report(previous)
        self.recordset.set_report({self._model_name: report})

    def _record_lines(self):
        return self.record.get_data()

    def _load_mapper_options(self):
        return {
            'override_existing': self.recordset.override_existing
        }

    def run(self, record, **kw):
        """Run the import machinery!"""

        self.record = record
        if not self.record:
            # maybe deleted???
            msg = 'NO RECORD FOUND, maybe deleted? Check your jobs!'
            logger.error(msg)
            return

        self._init(self.record.recordset_id)

        mapper_options = self._load_mapper_options()

        for line in self._record_lines():
            line = self.cleanup_line(line)
            self.prepare_line(line)

            odoo_record = None

            try:
                with self.env.cr.savepoint():
                    values = self.mapper.map_record(line).values(
                        **mapper_options)
            except Exception, err:
                values = {}
                self._log_error(values, line, odoo_record, message=err)
                if self._break_on_error:
                    raise
                continue

            # handle forced skipping
            skip_info = self.skip_it(values, line)
            if skip_info:
                self._log_skipped(values, line, skip_info)
                continue

            try:
                with self.env.cr.savepoint():
                    if self.exists(values, line):
                        odoo_record = self.write(values, line)
                        self._log_updated(values, line, odoo_record)
                    else:
                        odoo_record = self.create(values, line)
                        self._log_created(values, line, odoo_record)
            except Exception, err:
                self._log_error(values, line, odoo_record, message=err)
                if self._break_on_error:
                    raise
                continue

        # update report
        self._do_report()

        # log chunk finished
        msg = ' '.join([
            'CHUNK FINISHED',
            '[created: {created}]',
            '[updated: {updated}]',
            '[skipped: {skipped}]',
            '[errored: {errored}]',
        ]).format(**self.chunk_report.counters())
        self._log(msg)

        chunk_finished_event.fire(
            self.env, self.model._name, self.record)

    def after_all(self, recordset):
        """Get something done after all the children jobs have completed.

        This should be triggered by `chunk_finished_event`.
        """
        # TODO: needed for logger and other stuff. Can be simplified.
        self._init(recordset)
