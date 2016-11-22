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
from __future__ import absolute_import
from openerp.osv import fields
from openerp.addons.connector.exception import ManyIDSInBackend
from openerp.addons.connector.connector import Binder
from ..backend import salesforce_backend


@salesforce_backend
class SalesforceBinder(Binder):
    """ Manage bindings between Models identifier and Salesforce identifier"""
    _model_name = []

    def to_openerp(self, salesforce_id, unwrap=False):
        """Returns the Odoo id for an external ID""

        :param salesforce_id: salesforce_id row unique idenifier
        :type salesforce_id: str

        :param unwrap: If True returns the id of the record related
                       to the binding record

        :return: id of binding or if unwrapped the id of the record related
                 to the binding record
        :rtype: int
        """
        with self.session.change_context({'active_test': False}):
            binding_ids = self.session.search(
                self.model._name,
                [('salesforce_id', '=', salesforce_id),
                 ('backend_id', '=', self.backend_record.id)],

            )
        if not binding_ids:
            return None
        assert len(binding_ids) == 1, "Several records found: %s" % binding_ids
        binding_id = binding_ids[0]
        if unwrap:
            return self.session.read(self.model._name,
                                     binding_id,
                                     ['openerp_id'])['openerp_id'][0]
        else:
            return binding_id

    def to_backend(self, binding_id):
        """Return the external code for a given binding model id

        :param binding_id: id of a binding model
        :type binding_id: int

        :return: external code of `binding_id` or None
        """
        sf_record = self.session.read(self.model._name,
                                      binding_id,
                                      ['salesforce_id'])
        if not sf_record:
            return None
        return sf_record['salesforce_id']

    def to_binding(self, record_id):
        """Return the binding id for a given openerp record and backend

        :param record_id: id of a Odoo record
        :type binding_id: int

        :return: external binding id for `record_id` or None
        """
        sf_id = self.session.search(
            self.model._name,
            [
                ('backend_id', '=', self.backend_record.id),
                ('openerp_id', '=', record_id)
            ]
        )
        if not sf_id:
            return None
        if len(sf_id) > 1:
            raise ManyIDSInBackend(
                'Many record found in backend %s for model %s record_id %s' %
                (self.backend_record.name, self.model._name, record_id)
            )
        return sf_id[0]

    def bind(self, salesforce_id, binding_id):
        """ Create the link between an external id and an Odoo row and
        by updating the last synchronization date and the external code.

        :param external_id: Salesforce unique identifier
        :param binding_id: Binding record id
        :type binding_id: int or long
        """
        # avoid to trigger the export when we modify the `odbc code`
        context = self.session.context.copy()
        context['connector_no_export'] = True
        now_fmt = fields.datetime.now()
        self.environment.model.write(self.session.cr,
                                     self.session.uid,
                                     binding_id,
                                     {'salesforce_id': salesforce_id,
                                      'salesforce_sync_date': now_fmt},
                                     context=context)
