# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import ImportSynchronizer
from openerp.addons.connector.exception import IDMissingInBackend
from ..unit.rest_api_adapter import with_retry_on_expiration

_logger = logging.getLogger('salesforce_import_synchronizer')


class SalesforceImportSynchronizer(ImportSynchronizer):

    def __init__(self, connector_env):
        super(SalesforceImportSynchronizer, self).__init__(connector_env)
        self.salesforce_id = None
        self.salesforce_record = None

    def _after_import(self, binding_id):
        """ Hook called after the import"""
        return

    def _before_import(self):
        """ Hook called before the import"""
        return

    def _create(self, data):
        return self.session.create(self.model._name, data)

    def _deactivate(self):
        assert self.salesforce_id
        model = self.session.pool[self.model._name]
        cols = set(model._columns.keys())
        cols.update(model._inherit_fields.keys())
        if 'active' not in cols:
            raise NotImplementedError(
                'Model %s does not have an active field. '
                'custom _deactivate must be implemented'
            )
        current_id = self.binder.to_openerp(self.salesforce_id)
        self.session.write(self.model._name,
                           [current_id],
                           {'active': False})

    def _get_record(self):
        return self.backend_adapter.read(self.salesforce_id)

    def _map_data_for_update(self, mapper, **kwargs):
        """ Call the convert function of the Mapper

        in order to get converted record by using
        mapper.data or mapper.data_for_create

        :return: mapped dic of data to be used by
                 :py:meth:``models.Model.create``
        :rtype: dict
        """
        data = mapper.values(**kwargs)
        self._validate_data(data)
        return data

    def _map_data_for_create(self, mapper, **kwargs):
        """ Call the convert function of the Mapper

        in order to get converted record by using
        mapper.data or mapper.data_for_create

        :return: mapped dic of data to be used by
                 :py:meth:``models.Model.create``
        :rtype: dict
        """
        data = mapper.values(for_create=True, **kwargs)
        self._validate_data(data)
        return data

    def _update(self, binding_id, data):
        self.session.write(self.model._name, binding_id, data)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        :param data: data to validate
        Proactively check before the ``_create`` or
        ``_update`` if some fields are missing or invalid.

        Raise `InvalidDataError`
        """
        # we may want to return an NotImplementedError
        return

    def _import(self, binding_id):
        record_mapper = self.mapper.map_record(self.salesforce_record)
        if binding_id:
            # optimisation trick to avoid lookup binding
            data = self._map_data_for_update(record_mapper,
                                             binding_id=binding_id,
                                             backend_record=self.backend_record)
            self._update(binding_id, data)
        else:
            data = self._map_data_for_create(record_mapper,
                                             binding_id=binding_id,
                                             backend_record=self.backend_record)
            binding_id = self._create(data)
        self.binder.bind(self.salesforce_id, binding_id)
        self._after_import(binding_id)

    def run(self, salesforce_id, deactivate=False):
        self.salesforce_id = salesforce_id
        if deactivate:
            self._deactivate()
            return
        self.salesforce_record = self._get_record()
        if not self.salesforce_record:
            raise IDMissingInBackend(
                'id %s does not exists in Salesforce for %s' % (
                    self.backend_adapter._sf_type
                )
            )
        self._before_import()
        binding_id = self.binder.to_openerp(self.salesforce_id)
        # calls _after_import
        self._import(binding_id)


class SalesforceBatchSynchronizer(ImportSynchronizer):

    def before_batch_import(self):
        pass

    def after_batch_import(self):
        pass

    def run(self, date=False):
        self.before_batch_import()
        salesforce_ids = self.backend_adapter.get_updated(date)
        for salesforce_id in salesforce_ids:
            self._import_record(salesforce_id)
        salesforce_ids = self.backend_adapter.get_deleted(date)
        for salesforce_id in salesforce_ids:
            self._deactivate_record(salesforce_id)
        self.after_batch_import()

    def _import_record(self, salesforce_id):
        """ Import a record directly or delay the import of the record.
        Method to implement in sub-classes.
        """
        raise NotImplementedError

    def _deactivate_record(self, salesforce_id):
        """ Import a record directly or delay the import of the record.
        Method to implement in sub-classes.
        """
        raise NotImplementedError


class SalesforceDelayedBatchSynchronizer(SalesforceBatchSynchronizer):

    def _import_record(self, salesforce_id):
        import_record.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            salesforce_id)

    def _deactivate_record(self, salesforce_id):
        deactivate_record.delay(self.session,
                                self.model._name,
                                self.backend_record.id,
                                salesforce_id)


class SalesforceDirectBatchSynchronizer(SalesforceBatchSynchronizer):

    def _import_record(self, salesforce_id):
        import_record(self.session,
                      self.model._name,
                      self.backend_record.id,
                      salesforce_id)

    def _deactivate_record(self, salesforce_id):
        deactivate_record(self.session,
                          self.model._name,
                          self.backend_record.id,
                          salesforce_id)


@with_retry_on_expiration
def batch_import(session, model_name, backend_id, date=False):
    backend = session.browse(
        'connector.salesforce.backend',
        backend_id
    )
    connector_env = backend.get_connector_environment(model_name)
    importer = connector_env.get_connector_unit(
        SalesforceDirectBatchSynchronizer
    )
    importer.run(date=date)


@with_retry_on_expiration
def delayed_batch_import(session, model_name, backend_id, date=False):
    backend = session.browse(
        'connector.salesforce.backend',
        backend_id
    )
    connector_env = backend.get_connector_environment(model_name)
    importer = connector_env.get_connector_unit(
        SalesforceDelayedBatchSynchronizer
    )
    importer.run(date=date)


@job
def import_record(session, model_name, backend_id, salesforce_id):
    backend = session.browse(
        'connector.salesforce.backend',
        backend_id
    )
    connector_env = backend.get_connector_environment(model_name)
    importer = connector_env.get_connector_unit(
        SalesforceImportSynchronizer
    )
    importer.run(salesforce_id)


@job
def deactivate_record(session, model_name, backend_id, salesforce_id):
    backend = session.browse(
        'connector.salesforce.backend',
        backend_id
    )
    connector_env = backend.get_connector_environment(model_name)
    importer = connector_env.get_connector_unit(
        SalesforceImportSynchronizer
    )
    importer.run(salesforce_id, deactivate=True)
