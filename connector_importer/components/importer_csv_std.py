# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component

from ..log import logger


class RecordImporterCSVStd(Component):
    """CSV Standard importer for records.

    This importer is used to import standard CSV files, using the `load()`
    method of Odoo.
    """

    _name = 'importer.record.csv.std'
    _inherit = ['importer.record']
    _break_on_error = True  # We want the import to stop if an error occurs

    @property
    def mapper(self):
        if not self._mapper:
            self._mapper = self.component(usage='importer.mapper.csv.std')
        return self._mapper

    def prepare_load_params(self, lines):
        """Prepare the parameters for the `load()` standard method.

        It returns a list of fieldnames + the list of corresponding values.
        """
        fieldnames = list(lines[0].keys())

        data = [
            [line[fieldname] for fieldname in fieldnames]
            for line in lines
        ]
        return fieldnames, data

    def run(self, record, is_last_importer=True, **kw):
        """Run record job.

        Steps:

        * for each record, check if it is already imported or not and reference
          them as created or updated
        * launch the import with 'load()' method
        * analyse error messages returned by 'load()' and remove relevant
          references from the first step + create log error for them
        * produce a report and store it on recordset
        """

        self.record = record
        if not self.record:
            # maybe deleted???
            msg = 'NO RECORD FOUND, maybe deleted? Check your jobs!'
            logger.error(msg)
            return

        self._init_importer(self.record.recordset_id)

        mapped_lines = []
        tracker_data = {
            'created': {
                # line_nr: (values, line, odoo_record),
            },
            'updated': {
                # line_nr: (values, line, odoo_record),
            },
        }
        lines = self._record_lines()
        for i, line in enumerate(lines):
            line = self.prepare_line(line)
            options = self._load_mapper_options()
            try:
                with self.env.cr.savepoint():
                    values = self.mapper.map_record(line).values(**options)
                logger.debug(values)
            except Exception as err:
                values = {}
                self.tracker.log_error(
                    values, line, odoo_record=None, message=err)
                if self._break_on_error:
                    raise
                continue
            # Collect tracker data for later
            # We store the parameters for chunk_report.track_{created,updated}
            # functions, excepted the odoo_record which could not be known
            # for newly created records
            odoo_record_exists = self.record_handler.odoo_exists(
                values, line, use_xmlid=True)
            if odoo_record_exists:
                odoo_record = self.record_handler.odoo_find(
                    values, line, use_xmlid=True)
                tracker_data['updated'][i] = [line, odoo_record]
            else:
                tracker_data['created'][i] = [line, None]

            # handle forced skipping
            skip_info = self.skip_it(values, line)
            if skip_info:
                self.tracker.log_skipped(values, line, skip_info)
                continue
            mapped_lines.append(values)

        if mapped_lines:
            try:
                with self.env.cr.savepoint():
                    fieldnames, data = self.prepare_load_params(mapped_lines)
                    load_res = self.model.load(fieldnames, data)

                    # Log load errors
                    for message in load_res['messages']:
                        if message.get('rows'):
                            line_numbers = range(
                                message['rows']['from'],
                                message['rows']['to'] + 1)
                            for line_nr in line_numbers:
                                # First we remove the entry from tracker data
                                tracker_data['created'].pop(line_nr, None)
                                tracker_data['updated'].pop(line_nr, None)
                                # We add 2 as the tracker count lines starting
                                # from 1 + header line
                                line = {'_line_nr': line_nr + 2}
                                self.tracker.log_error(
                                    {}, line, odoo_record=None,
                                    message=message['message'])
                        else:
                            line = {'_line_nr': 0}
                            self.tracker.log_error(
                                {}, line, odoo_record=None,
                                message=message['message'])
            except Exception as err:
                line = {'_line_nr': 0}
                self.tracker.log_error(
                    {}, line, odoo_record=None, message=err)
                if self._break_on_error:
                    raise

        # Record the tracker data for the report
        # We are using 'tracker.chunk_report' methods instead of 'tracker'
        # as the formers don't require an 'odoo_record' (which we don't have)
        for args in tracker_data['created'].values():
            self.tracker.chunk_report.track_created(
                self.tracker.chunk_report_item(*args))
        for args in tracker_data['updated'].values():
            self.tracker.chunk_report.track_updated(
                self.tracker.chunk_report_item(*args))

        # update report
        self._do_report()

        # log chunk finished
        msg = ' '.join([
            'CHUNK FINISHED',
            '[created: {created}]',
            '[updated: {updated}]',
            '[skipped: {skipped}]',
            '[errored: {errored}]',
        ]).format(**self.tracker.get_counters())
        self.tracker._log(msg)

        # TODO
        # chunk_finished_event.fire(
        #     self.env, self.model._name, self.record)
        return 'ok'
