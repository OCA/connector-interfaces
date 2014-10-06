# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.connector.unit.synchronizer import ImportSynchronizer
from openerp.addons.connector.exception import (IDMissingInBackend,
                                                ManyIDSInBackend)
from openerp.addons.connector.queue.job import job

_logger = logging.getLogger(__name__)

# For direct import we may want to import by chunk
# in order not too eat too munch memory on PostgreSQL side
MAX_PROC_BLOC = 2000
# do an intermediate commit for each bloc
BLOC_COMMIT = True


class ODBCSynchronizer(ImportSynchronizer):
    """Base connector ODBC importer"""

    def __init__(self, environment):
        """
        :param environment: connector Environment
        :type environment: :py:class:`connector.connector.Environment`
        """
        super(ODBCSynchronizer, self).__init__(environment)

    def _get_odbc_data(self):
        """ Return the raw query data of given ODBC code
        :return: an pyodbc row see https://code.google.com/p/pyodbc/wiki/Rows
        """
        # read return a generator
        res = list(self.backend_adapter.read(self.odbc_code, self.data_set))
        if not res:
            raise IDMissingInBackend(
                'No value found for %s %s' % (self.model._name,
                                              self.odbc_code)
            )
        if len(res) > 1:
            raise ManyIDSInBackend(
                'Many value found for %s %s' % (self.model._name,
                                                self.odbc_code)
            )
        return res[0]

    def _before_import(self):
        """ Hook called before the import, when we have the ODBC data
        data"""
        return

    def _get_odbc_revelant_update_date(self):
        """Return the date determining last update of current row
        doing a lookup on create and update time

        :return: last update date of current row
        :rtype: datetime.datetime or None
        """
        dates = [
            getattr(self.odbc_code, 'create_time', False),
            getattr(self.odbc_code, 'modify_time', False)
        ]
        filtered_dates = [x for x in dates if x]
        if not filtered_dates:
            return None
        return max(filtered_dates)

    def _is_uptodate(self, binding_id):
        """Predicate that checks if the import should be skipped because
        it is already up-to-date in Odoo

        :param binding_id: id of the binding record
        :type binding_id: int

        :return: True is current row is up to date
        :rtype: bool
        """
        assert self.odbc_record
        if not binding_id:
            return False
        binding = self.session.browse(self.model._name, binding_id)
        local_sync_date = binding.sync_date
        if not local_sync_date:
            return
        local_sync_date = datetime.strptime(local_sync_date,
                                            DEFAULT_SERVER_DATETIME_FORMAT)
        odbc_date = self._get_odbc_revelant_update_date()
        if not odbc_date:
            return False
        return local_sync_date < odbc_date

    def _map_data(self):
        """ Call the convert function of the Mapper

        in order to get converted record by using
        mapper.data or mapper.data_for_create

        :return: mapped dic of data to be used by
                 :py:meth:``models.Model.create``
        :rtype: dict
        """
        return self.mapper.map_record(self.odbc_record)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        :param data: data to validate
        Proactively check before the ``_create`` or
        ``_update`` if some fields are missing or invalid.

        Raise `InvalidDataError`
        """
        # we may want to return an NotImplementedError
        return

    def _deactivate(self, binding_id):
        """Deactivate an Odoo model

        :param binding_id: id of the binding record

        :return: id of the binding record
        :rtype: int
        """
        if not binding_id:
            raise ValueError('Deactivate code can not be empty')
        if 'active' in self.model._fields:
            self.session.write(self.model._name, binding_id, {'active': False})
        else:
            raise AttributeError(
                'Model %s does not have "active" col' % self.model._name
            )
        return binding_id

    def _create(self, data):
        """ Create the OpenERP record of current ODBC row

        :param data: dict of data to be used by
                     :py:meth:``models.Model.create``

        :return: created row id
        :rtype: int
        """
        return self.session.create(self.model._name, data)

    def _update(self, binding_id, data):
        """ Update the binding record of current ODBC row

        :param binding_id: id of the binding record
        :param data: dict of data to be used by
                     :py:meth:``models.Model.create``

        :return: Success bool
        :rtype: bool
        """
        return self.session.write(self.model._name, binding_id, data)

    def _after_import(self, binding_id):
        """Hook called at the end of the import
        :param binding_id: id of the binding record
        """
        return

    def run(self, model_name, odbc_code):
        """Run the synchronization for given model
        and external code

        :param model_name: list of Odoo model name taken form `_name` property
        :param odbc_code: External system code
        """
        self.odbc_code = odbc_code
        self._before_import()
        try:
            self.odbc_record = self._get_odbc_data()
        except IDMissingInBackend:
            # We do this here atop of missing in case
            # We use existing openerp_id as base
            binding_id = self.binder.to_openerp(self.odbc_code)
            self._deactivate(binding_id)
            return
        binding_id = self.binder.to_openerp(odbc_code)
        if self._is_uptodate(binding_id):
            return _('Record %s %s allready up-to-date') % (self.model._name,
                                                            odbc_code)
        # performance tweak
        if binding_id:
            self.mapper.binding_id = binding_id
        record_mapper = self._map_data()

        if binding_id:
            record = record_mapper.values()
            self._validate_data(record)
            self._update(binding_id, record)
        else:
            record = record_mapper.values(for_create=True)
            self._validate_data(record)
            binding_id = self._create(record)

        self.binder.bind(self.odbc_code, binding_id)
        self._after_import(binding_id)


class BatchODBCSynchronizer(ImportSynchronizer):
    """Base importer class for odbc batch import"""

    def __init__(self, environment):
        super(BatchODBCSynchronizer, self).__init__(environment)

    def _before_batch_import(self):
        """Hook called before import"""
        return

    def _after_batch_import(self):
        """Hook call after import"""
        return

    def _import_record(self, odbc_code):
        """Synchronize external row for given code
        :param odbc_code: External system code

        Abstact method
        """

        raise NotImplementedError('Record importation not implemented')

    def run(self, model_name, date=False):
        """Run the synchronization for given model
        at lookup date

        :param model_name: list of Odoo model name taken form `_name` property
        :param date: past lookup date for external data
        """
        self._before_batch_import()
        codes = self.backend_adapter.search(date=date)
        for code in codes:
            self._import_record(code)
        self._after_batch_import()


class DirectBatchODBCSynchronizer(BatchODBCSynchronizer):
    """Base connector ODBC batch importer class without jobs"""

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.Environment`
        """
        super(BatchODBCSynchronizer, self).__init__(environment)

    def run(self, model_name, date=False, direct=False):
        """Run the synchronization for all the rows of given model

        :param model_name: Odoo model name taken form `_name` property
        :param date: past lookup date for external data
        :type date: date string
        :param direct: if True no job will be used
        """
        self._before_batch_import()
        _logger.debug("Direct batch import of %s started" % model_name)
        codes = self.backend_adapter.search(date=date)
        for codes_chunk in [codes[i:i + MAX_PROC_BLOC]
                            for i in xrange(0, len(codes), MAX_PROC_BLOC)]:
            data = list(self.backend_adapter.read(codes_chunk))
            for code in codes_chunk:
                self._import_record(code, data_set=data)
            if BLOC_COMMIT:
                self.session.cr.commit()
        existing_ids = self.session.search(self.model._name, [])
        codes_to_check = self.session.read(self.model._name,
                                           existing_ids,
                                           ['odbc_code'])
        codes_to_check = [x['odbc_code'] for x in codes_to_check]

        # looking for data deleted in backend
        missing = self.backend_adapter.missing(codes_to_check)
        for codes_chunk in [missing[i:i + MAX_PROC_BLOC]
                            for i in xrange(0, len(missing), MAX_PROC_BLOC)]:
            for code in codes_chunk:
                self._import_record(code)
        if BLOC_COMMIT:
            self.session.cr.commit()

        self._after_batch_import()

        _logger.debug("Direct batch import of %s ended" % model_name)

    def _import_record(self, odbc_code, data_set=False):
        """Synchronize external row for given code
        :param odbc_code: External system code
        :param data_set: performace memoizer dict
        :type data_set: dict

        """
        record_import(self.session,
                      self.model._name,
                      self.backend_record.id,
                      odbc_code,
                      data_set=data_set)


class DelayedBatchODBCSynchronizer(BatchODBCSynchronizer):
    """Base batch connector ODBC using jobs"""

    def _import_record(self, odbc_code):
        """Synchronize external row for given code
        :param odbc_code: External system code
        :param data_set: performace memoizer dict

        """
        register = self.backend_record._get_register(self.model._name)
        model = register.model_id
        msg = 'Importing %s using connector odbc' % model.name

        priority = register.sequence
        record_import.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            odbc_code,
                            description=msg,
                            priority=priority)


def batch_import(session, model_name, backend_id, date=False):
    """Run the synchronization for given model
    at lookup date

    :param model_name: list of Odoo model name taken form `_name` property
    :param data_set: performace memoizer dict
    :param backend_id: id of current connector ODBC backend
    """
    env = session.browse('connector.odbc.data.server.backend',
                         backend_id).get_environment(model_name)
    importer = env.get_connector_unit(DirectBatchODBCSynchronizer)
    importer.run(model_name, date=date)


@job
def record_import(session, model_name, backend_id, odbc_code, data_set=None):
    """Synchronize external row for given code

    :param model_name: list of Odoo model name taken form `_name` property
    :param data_set: performace memoizer dict
    :param backend_id: id of current connector ODBC backend
    :param odbc_code: External system code
    :param date: past lookup date for external data

    """
    env = session.browse('connector.odbc.data.server.backend',
                         backend_id).get_environment(model_name)
    importer = env.get_connector_unit(ODBCSynchronizer)
    importer.data_set = data_set
    importer.run(model_name, odbc_code)


@job
def delayed_batch_import(session, model_name, backend_id, date=False):
    """Run the synchronization for given model
    at lookup date using jobs

    :param model_name: list of Odoo model name taken form `_name` property
    :param data_set: performace memoizer dict
    :param backend_id: id of current connector ODBC backend
    """
    env = session.browse('connector.odbc.data.server.backend',
                         backend_id).get_environment(model_name)
    importer = env.get_connector_unit(DelayedBatchODBCSynchronizer)
    importer.run(model_name, date=date)
