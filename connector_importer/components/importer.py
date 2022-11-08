# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, exceptions

from odoo.addons.component.core import Component

from ..log import LOGGER_NAME, logger


class RecordSetImporter(Component):
    """Importer for recordsets."""

    _name = "importer.recordset"
    _inherit = "importer.base.component"
    _usage = "recordset.importer"
    _apply_on = "import.recordset"

    def run(self, recordset, **kw):
        """Run recordset job.

        Steps:

        * update last start date on recordset
        * read source
        * process all source lines in chunks
        * create an import record per each chunk
        * schedule import for each record
        """
        # reset recordset
        recordset._prepare_for_import_session()
        msg = "START RECORDSET {} ({})".format(recordset.name, recordset.id)
        logger.info(msg)
        # flush existing records as we are going to re-create them
        source = recordset.get_source()
        if not source:
            raise exceptions.UserError(
                _("No source configured on recordset '%s'") % recordset.name
            )
        for chunk in source.get_lines():
            # create chuncked records and run their imports
            record = self.env["import.record"].create({"recordset_id": recordset.id})
            # store data
            record.set_data(chunk)
            record.run_import()


class RecordImporter(Component):
    """Importer for records.

    This importer is actually the one that does the real import work.
    It loads each import records and tries to import them
    and keep tracks of errored, skipped, etc.
    See `run` method for detailed information on what it does.
    """

    _name = "importer.record"
    _inherit = ["importer.base.component"]
    _usage = "record.importer"
    # log and report errors
    # do not make the whole import fail
    _break_on_error = False
    _record_handler_usage = "odoorecord.handler"
    _tracking_handler_usage = "tracking.handler"
    # a unique key (field name) to retrieve the odoo record
    # if this key is an external/XML ID, prefix the name with `xid::` (eg: xid::id)
    odoo_unique_key = ""

    def _init_importer(self, recordset):
        self.recordset = recordset
        # record handler is responsible for create/write on odoo records
        self.record_handler = self.component(usage=self._record_handler_usage)
        self.record_handler._init_handler(
            importer=self,
            unique_key=self.unique_key,
        )
        # tracking handler is responsible for logging and chunk reports
        self.tracker = self.component(usage=self._tracking_handler_usage)
        self.tracker._init_handler(
            model_name=self.model._name,
            logger_name=LOGGER_NAME,
            log_prefix=self.recordset.import_type_id.key + " ",
        )
        # TODO: trash on v16
        # `odoo_unique_key_is_xmlid` has been deprecated from v15
        if hasattr(self, "odoo_unique_key_is_xmlid"):
            raise AttributeError("`odoo_unique_key_is_xmlid` is not supported anymore")

    @property
    def unique_key(self):
        return self.work.options.importer.get("odoo_unique_key", self.odoo_unique_key)

    @property
    def unique_key_is_xmlid(self):
        return self.unique_key.startswith("xid::") or self.unique_key == "id"

    # Override to not rely on automatic mapper lookup.
    # This is especially needed if you register more than one importer
    # for a given odoo model. Eg: 2 importers for res.partner
    # (1 for customers and 1 for suppliers)
    _mapper_name = None
    _mapper_usage = "importer.mapper"
    # just an instance cache for the mapper
    _mapper = None

    # TODO: do the same for record handler and tracking handler
    def _get_mapper(self):
        mapper_name = self.work.options.mapper.get("name", self._mapper_name)
        if mapper_name:
            return self.component_by_name(mapper_name)
        mapper_usage = self.work.options.mapper.get("usage", self._mapper_usage)
        return self.component(usage=mapper_usage)

    @property
    def mapper(self):
        if not self._mapper:
            self._mapper = self._get_mapper()
        return self._mapper

    @property
    def must_break_on_error(self):
        return self.work.options.importer.get("break_on_error", self._break_on_error)

    @property
    def must_override_existing(self):
        return self.work.options.importer.get(
            "override_existing", self.recordset.override_existing
        )

    def required_keys(self, create=False):
        """Keys that are mandatory to import a line."""
        req = self.mapper.required_keys()
        all_values = []
        for k, v in req.items():
            # make sure values are always tuples
            # as we support multiple dest keys
            if not isinstance(v, (tuple, list)):
                req[k] = (v,)
            all_values.extend(req[k])
        unique_key = self.unique_key
        if (
            unique_key
            and unique_key not in list(req.keys())
            and unique_key not in all_values
        ):
            # this one is REALLY required :)
            req[unique_key] = (unique_key,)
        return req

    # mostly for auto-documentation in UI
    def default_values(self):
        """Values that are automatically assigned."""
        return self.mapper.default_values()

    def translatable_keys(self, create=False):
        """Keys that are translatable."""
        return self.mapper.translatable_keys()

    def translatable_langs(self):
        return self.env["res.lang"].search([("active", "=", True)]).mapped("code")

    def make_translation_key(self, key, lang):
        sep = self.work.options.importer.get("translation_key_sep", ":")
        regional_lang = self.work.options.importer.get(
            "translation_use_regional_lang", False
        )
        if not regional_lang:
            lang = lang[:2]  # eg: "de_DE" -> "de"
        return f"{key}{sep}{lang}"

    def collect_translatable(self, values, orig_values):
        """Get translations values for `mapper.translatable_keys`.

        We assume that the source contains translatable columns in the form:

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

    def _check_missing(self, source_key, dest_key, values, orig_values):
        """Check for required keys missing."""
        missing = (
            not source_key.startswith("__") and orig_values.get(source_key) is None
        )
        unique_key = self.unique_key
        if missing:
            msg = "MISSING REQUIRED SOURCE KEY={}".format(source_key)
            if unique_key and values.get(unique_key):
                msg += ": {}={}".format(unique_key, values[unique_key])
            return {"message": msg}
        missing = not dest_key.startswith("__") and values.get(dest_key) is None
        is_xmlid = dest_key == unique_key and self.unique_key_is_xmlid
        if missing and not is_xmlid:
            msg = "MISSING REQUIRED DESTINATION KEY={}".format(dest_key)
            if unique_key and values.get(unique_key):
                msg += ": {}={}".format(unique_key, values[unique_key])
            return {"message": msg}
        return False

    def skip_it(self, values, orig_values):
        """Skip item import conditionally... if you want ;).

        You can return back `False` to not skip
        or a dictionary containing info about skip reason.
        """
        msg = ""
        required = self.required_keys()
        for source_key, dest_key in required.items():
            # we support multiple destination keys
            for _dest_key in dest_key:
                missing = self._check_missing(
                    source_key, _dest_key, values, orig_values
                )
                if missing:
                    return missing

        if (
            self.record_handler.odoo_exists(values, orig_values)
            and not self.must_override_existing
        ):
            msg = "ALREADY EXISTS"
            if self.unique_key:
                msg += ": {}={}".format(self.unique_key, values[self.unique_key])
            return {
                "message": msg,
                "odoo_record": self.record_handler.odoo_find(values, orig_values).id,
            }
        return False

    def _cleanup_line(self, line):
        """Apply basic cleanup on lines."""
        # we cannot alter dict keys while iterating
        res = {}
        for k, v in line.items():
            # skip internal tech keys if any
            if not k.startswith("_"):
                k = self.clean_line_key(k)
            if isinstance(v, str):
                v = v.strip()
            res[k] = v
        return res

    def clean_line_key(self, key):
        """Clean record key.

        Sometimes your CSV source do not have proper keys,
        they can contain a lot of crap or they can change
        lower/uppercase from import to importer.
        You can override this method to normalize keys
        and make your import mappers work reliably.
        """
        return key.strip()

    def prepare_line(self, line):
        """Pre-manipulate a line if needed.

        For instance: you might want to fix some field names.
        Sometimes in CSV you have mispelled names
        (upper/lowercase, spaces, etc) all chars that might break your mappers.

        Here you can adapt the source line before the mapper is called
        so that the logic in the mapper will be always the same.
        """
        return self._cleanup_line(line)

    def _do_report(self):
        """Update recordset report using the tracker."""
        previous = self.recordset.get_report()
        report = self.tracker.get_report(previous)
        self.recordset.set_report({self.model._name: report})

    def _record_lines(self):
        """Get lines from import record."""
        return self.record.get_data()

    def _load_mapper_options(self):
        """Retrieve mapper options."""
        return {"override_existing": self.must_override_existing}

    # TODO: make these contexts customizable via recordset settings
    def _odoo_default_context(self):
        """Default context to be used in both create and write methods"""
        return {
            "importer_type_id": self.recordset.import_type_id.id,
            "tracking_disable": True,
        }

    def _odoo_create_context(self):
        """Inject context variables on create, merged by odoorecord handler."""
        return self._odoo_default_context()

    def _odoo_write_context(self):
        """Inject context variables on write, merged by odoorecord handler."""
        return self._odoo_default_context()

    def run(self, record, is_last_importer=True, **kw):
        """Run record job.

        Steps:

        * check if record is still available
        * initialize the import
        * read each line to be imported
        * clean them up
        * manipulate them (field names fixes and such)
        * retrieve a mapper and convert values
        * check and skip record if needed
        * if record exists: update it, else, create it
        * produce a report and store it on recordset
        """

        self.record = record
        if not self.record:
            # maybe deleted???
            msg = "NO RECORD FOUND, maybe deleted? Check your jobs!"
            logger.error(msg)
            return

        self._init_importer(self.record.recordset_id)
        for line in self._record_lines():
            line = self.prepare_line(line)
            options = self._load_mapper_options()

            odoo_record = None

            try:
                with self.env.cr.savepoint():
                    values = self.mapper.map_record(line).values(**options)
                logger.debug(values)
            except Exception as err:
                values = {}
                self.tracker.log_error(values, line, odoo_record, message=err)
                if self.must_break_on_error:
                    raise
                continue

            # handle forced skipping
            skip_info = self.skip_it(values, line)
            if skip_info:
                self.tracker.log_skipped(values, line, skip_info)
                continue

            try:
                with self.env.cr.savepoint():
                    if self.record_handler.odoo_exists(values, line):
                        odoo_record = self.record_handler.odoo_write(values, line)
                        self.tracker.log_updated(values, line, odoo_record)
                    else:
                        if self.work.options.importer.write_only:
                            self.tracker.log_skipped(
                                values,
                                line,
                                {"message": "Write-only importer, record not found."},
                            )
                            continue
                        odoo_record = self.record_handler.odoo_create(values, line)
                        self.tracker.log_created(values, line, odoo_record)
            except Exception as err:
                self.tracker.log_error(values, line, odoo_record, message=err)
                if self.must_break_on_error:
                    raise
                continue

        # update report
        self._do_report()

        # log chunk finished
        counters = self.tracker.get_counters()
        msg = " ".join(
            [
                "CHUNK FINISHED",
                "[created: {created}]",
                "[updated: {updated}]",
                "[skipped: {skipped}]",
                "[errored: {errored}]",
            ]
        ).format(**counters)
        self.tracker._log(msg)
        self._trigger_finish_events(record, is_last_importer=is_last_importer)
        return counters

    def _trigger_finish_events(self, record, is_last_importer=False):
        """Trigger events when the importer has done its job."""
        if is_last_importer:
            # Trigger global event for recordset
            self.recordset._event(
                "on_last_record_import_finished", collection=self.work.collection
            ).notify(self, record)
            # Trigger model specific event
            self.model.browse()._event(
                "on_last_record_import_finished", collection=self.work.collection
            ).notify(self, record)
