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
from __future__ import absolute_import
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import orm
from openerp.addons.connector.connector import Binder
from openerp.addons.connector_odbc.backend import odbc_backend


@odbc_backend
class ODBCBinder(Binder):
    """ Manage bindings between Models identifier and ODBC identifier"""
    _model_name = []

    def to_openerp(self, odbc_code, unwrap=False):
        """Returns the Odoo id for an external ID""

        :param odbc_code: odbc row unique idenifier
        :type odbc_code: str

        :param unwrap: If True returns the id of the record related
                       to the binding record

        :return: id of binding or if unwrapped the id of the record related
                 to the binding record
        :rtype: int
        """
        binding_ids = self.session.search(
            self.model._name,
            [('odbc_code', '=', odbc_code),
             ('backend_id', '=', self.backend_record.id)]
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

        :return: external code of `binding_id`
        """
        odbc_record = self.session.read(self.model._name,
                                        binding_id,
                                        ['odbc_code'])
        assert odbc_record, 'No corresponding binding found'
        return odbc_record['odbc_code']

    @classmethod
    def register_external_binding(cls, binding_class):
        """ Register a binding model that inherits from external.binding
        :param binding_class: class to register
        """
        if not issubclass(binding_class, orm.Model):
            raise TypeError('You try to bind a non orm.Model subclass')

        #  We have no pooler access at class level
        def get_class(name):
            classes = orm.Model.__subclasses__()
            classes.extend(orm.AbstractModel.__subclasses__())
            for x in classes:
                if x._name == name:
                    return x
            return

        def parent_model(container, look_class):
            """ Return parent model list in orm.Model way"""
            inherit = getattr(look_class, '_inherit', None)
            if inherit:
                container.append(inherit)
                return parent_model(container, get_class(inherit))
            else:
                return container

        parents = parent_model([], binding_class)
        if "external.binding" not in parents:
            raise TypeError('You try to bin a model that does'
                            ' not inherit from external.binding')

        class_name = binding_class._name
        if class_name not in cls._model_name:
            cls._model_name.append(class_name)

    def bind(self, external_id, binding_id):
        """ Create the link between an external id and an Odoo row and
        by updating the last synchronization date and the external code.

        :param external_id: ODBC unique identifier
        :param binding_id: Binding record id
        :type binding_id: int
        """
        # avoid to trigger the export when we modify the `odbc code`
        context = self.session.context.copy()
        context['connector_no_export'] = True
        now_fmt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.environment.model.write(self.session.cr,
                                     self.session.uid,
                                     binding_id,
                                     {'odbc_code': external_id,
                                      'sync_date': now_fmt},
                                     context=context)

    def create_binding_from_record(self, external_id, internal_id):
        """Create a binding record for a exsiting Odoo record

        :param external_id: ODBC unique identifier
        :param internal_id: Odoo record id
        :type internal_id: int

        """
        now_fmt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return self.environment.model.create(
            self.session.cr,
            self.session.uid,
            {'odbc_code': external_id,
             'sync_date': now_fmt,
             'openerp_id': internal_id,
             'backend_id': self.backend_record.id},
            context=self.session.context
        )


def odbc_binded(cls):
    """ Register a binding model that inherits from external.binding
    :param cls: class to register
    """
    ODBCBinder.register_external_binding(cls)
    return cls
