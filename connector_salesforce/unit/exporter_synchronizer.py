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
from openerp.addons.connector.unit.synchronizer import ExportSynchronizer
from openerp.addons.connector.exception import IDMissingInBackend
from ..unit.rest_api_adapter import with_retry_on_expiration

_logger = logging.getLogger('salesforce_export_synchronizer')


class SalesforceExportSynchronizer(ExportSynchronizer):
    """Exproter to sales force external id is supported
    should  be use only if model is exported only.
    It is done by setting _sf_lookup in adapter to the name of external field.
    Switching from export to import direction is possible when using lookup
    but not the way around. To be able to do this all external fields
    must be field with SF Object Id.
    """

    def __init__(self, connector_env):
        super(SalesforceExportSynchronizer, self).__init__(connector_env)
        self.salesforce_id = None
        self.binding_record = None
        self.binding_id = None

    def _after_export(self, binding_id):
        """ Hook called after the export"""
        return

    def _before_export(self):
        """ Hook called before the export"""
        return

    def _deactivate(self):
        # external id not supported in delete
        # In Salesforce nothing is deleted it is just a flag
        # And deleted ind continue to exist into recycle bin.
        # Recycle bin lifespan is a Salesforce parameter
        # by default it is 15 days
        assert self.binding_record.salesforce_id
        if self.backend_adapter.exists(salesforce_id):
            self.backend_adapter.delete(self.binding_record.salesforce_id)

    def _to_deactivate(self):
        assert self.binding_record
        model = self.session.pool[self.model._name]
        cols = set(model._columns.keys())
        cols.update(model._inherit_fields.keys())
        if 'active' in cols:
            if not self.binding_record.active:
                return True
        return False

    def _get_record(self):
        assert self.binding_id
        return self.session.browse(
            self._model_name,
            self.binding_id
        )

    def _map_data_for_upsert(self, mapper, **kwargs):
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

    def _upsert(self, salesforce_id, data):
        sf_id = self.backend_adapter.upsert(salesforce_id, data)

    def _validate_data(self, data):
        """ Check if the values to export are correct

        :param data: data to validate
        Proactively check before the ``_upsert``
        if some fields are missing or invalid.

        Raise `InvalidDataError`
        """
        # we may want to return an NotImplementedError
        return

    def _export(self, binding_id, salesforce_id):
        record_mapper = self.mapper.map_record(self.binding_record)
        # optimisation trick to avoid lookup binding
        data = self._map_data_for_upsert(record_mapper,
                                         binding_id=binding_id,
                                         backend_record=self.backend_record)
        sf_id = self._upsert(salesforce_id, data)
        self.binder.bind(sf_id, binding_id)


    def run(self, binding_id, force_deactivate=False):
        self.binding_id = binding_id
        self.binding_record = self._get_record()
        if force_deactivate or self._to_deactivate():
            self._deactivate()
            return
        self._before_export()
        if self.binding_record.salesforce_id:
            self.salesforce_id = self.binding_record.salesforce_id
        else:
            if self.backend_adapter._sf_lookup:
                self.salesforce_id = binding_id
        # calls _after_export
        self._export(self.binding_id, self.salesforce_id)


class SalesforceBatchExportSynchronizer(ExportSynchronizer):

    def before_batch_export(self):
        pass

    def after_batch_export(self):
        pass

    def get_binding_ids_to_export(self, date=False):
        if not date:
            return self.session.search(
                self._model_name,
                []
            )
        else:
            return self.session.search(
                self._model_name,
                ['|',
                 ('salesforce_sync_date', '<', date),
                 ('salesforce_sync_date', '=', False)]
            )

    def run(self, date=False):
        for binding_id in self.get_binding_ids_to_export(date):
            self._export_record(binding_id)

    def _export_record(self, binding_id):
        """ Export a record directly or delay the export of the record.
        Method to implement in sub-classes.
        """
        raise NotImplementedError


class SalesforceDelayedBatchSynchronizer(SalesforceBatchExportSynchronizer):

    def _export_record(self, binding_id):
        export_record.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            binding_id)


class SalesforceDirectBatchSynchronizer(SalesforceBatchExportSynchronizer):

    def _export_record(self, binding_id):
        export_record(self.session,
                      self.model._name,
                      self.backend_record.id,
                      binding_id)


@with_retry_on_expiration
def batch_export(session, model_name, backend_id, date=False):
    backend = session.browse(
        'connector.salesforce.backend',
        backend_id
    )
    connector_env = backend.get_connector_environment(model_name)
    exporter = connector_env.get_connector_unit(
        SalesforceDirectBatchSynchronizer
    )
    exporter.run(date=date)


@with_retry_on_expiration
def delayed_batch_export(session, model_name, backend_id, date=False):
    backend = session.browse(
        'connector.salesforce.backend',
        backend_id
    )
    connector_env = backend.get_connector_environment(model_name)
    exporter = connector_env.get_connector_unit(
        SalesforceDelayedBatchSynchronizer
    )
    exporter.run(date=date)


@job
def export_record(session, model_name, backend_id, binding_id):
    backend = session.browse(
        'connector.salesforce.backend',
        backend_id
    )
    connector_env = backend.get_connector_environment(model_name)
    exporter = connector_env.get_connector_unit(
        SalesforceExportSynchronizer
    )
    exporter.run(binding_id)


@job
def deactivate_record(session, model_name, backend_id, binding_id):
    backend = session.browse(
        'connector.salesforce.backend',
        backend_id
    )
    connector_env = backend.get_connector_environment(model_name)
    exporter = connector_env.get_connector_unit(
        SalesforceExportSynchronizer
    )
    exporter.run(binding_id, deactivate=True)
