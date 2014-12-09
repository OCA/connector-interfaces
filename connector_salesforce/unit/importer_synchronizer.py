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
from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.synchronizer import ImportSynchronizer
from openerp.addons.connector.unit.mapper import ImportMapper
from openerp.addons.connector.exception import (IDMissingInBackend,
                                                RetryableJobError)
from ..backend import salesforce_backend

_logger = logging.getLogger('salesforce_import_synchronizer')


@salesforce_backend
class SalesforceImportSynchronizer(ImportSynchronizer):

    def __init__(self, connector_env):
        super(SalesforceImportSynchronizer, self).__init__(connector_env)
        self.sf_id
        self.sf_record

    def _after_import(self, binding_id):
        """ Hook called after the import"""
        return

    def _before_import(self):
        """ Hook called before the import"""
        return

    def _create(self, data):
        return self.session.create(self.model._name, data)

    def _get_record(self):
        return self.backend_adapter.read(self.sf_id)

    def _map_data_for_update(self, mapper, **kwargs):
        """ Call the convert function of the Mapper

        in order to get converted record by using
        mapper.data or mapper.data_for_create

        :return: mapped dic of data to be used by
                 :py:meth:``models.Model.create``
        :rtype: dict
        """
        self._validate_data(self.sf_record)
        return mapper.values(self.sf_record, **kwargs)

    def _map_data_for_create(self, mapper, **kwargs):
        """ Call the convert function of the Mapper

        in order to get converted record by using
        mapper.data or mapper.data_for_create

        :return: mapped dic of data to be used by
                 :py:meth:``models.Model.create``
        :rtype: dict
        """
        self._validate_data(self.sf_record)
        data = mapper.values(self.sf_record, for_create=True, **kwargs)
        self._validate_data(data)
        return data

    def _needs_update(self):
        pass

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
        record_mapper = self.mapper.map_record(self.sf_record)
        if binding_id:
            data = self._map_data_for_update(record_mapper)
            self._update(binding_id, data)
        else:
            data = self._map_data_for_create(self.sf_record)
            self._create(data)
        self.binder.bind(self.sf_id, binding_id)

    def run(self, sf_id, force=False):
        self.sf_id = sf_id
        self.record = self.get_record()
        if not self.record:
            raise IDMissingInBackend(
                'id %s does not exists in Salesforce for %s' % (
                    self.backend_adapter._sf_type
                )
            )
        self._before_import()
        binding_id = self.binder.to_openerp(self.sf_id)
        self._import(binding_id)
        self._after_import(binding_id)


@salesforce_backend
class SalesforceBatchSynchronizer(SalesforceImportSynchronizer):
    pass


@salesforce_backend
class SalesforceDelayedBatchSynchronizer(SalesforceBatchSynchronizer):
    pass


@salesforce_backend
class SalesforceDirectBatchSynchronizer(SalesforceBatchSynchronizer):
    pass
