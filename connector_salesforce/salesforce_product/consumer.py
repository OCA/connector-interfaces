# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2015 Camptocamp SA
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
from openerp.addons.connector.event import (on_record_write,
                                            on_record_create,
                                            on_record_unlink)
from ..consumer import delay_export, delay_deactivate
from ..unit.binder import SalesforceBinder


@on_record_create(model_names='connector.salesforce.product')
def export_sf_product(session, model_name, record_id, vals=None):
    """ Delay a job which export a product binding record.
    :param session: current session
    :type session: :py:class:`openerp.addons.connector.
                              session.ConnectorSession`

    :param model_name: name of the binding model.
                       In our case `connector.salesforce.xxx`
    :type model_name: str

    :record_id: The id of the binding model record
    :type record_id: int or long
    """
    record = session.browse(model_name, record_id)
    if record.backend_id.sf_product_master == 'erp':
        delay_export(session, model_name, record_id)


@on_record_unlink(model_names='connector.salesforce.product')
def deactivate_product(session, model_name, record_id):
    """ Delay a job which deactivate a binding product record
    on Salesforce

    :param session: current session
    :type session: :py:class:`openerp.addons.connector.
                              session.ConnectorSession`

    :param model_name: name of the binding model.
                       In our case `connector.salesforce.xxx`
    :type model_name: str

    :record_id: The id of the binding model record
    :type record_id: int or long
    """

    record = session.browse(model_name, record_id)
    if record.backend_id.sf_product_master == 'erp':
        delay_deactivate(session, model_name, record_id)


@on_record_create(model_names='product.product')
def create_product_binding(session, model_name, record_id, vals=None):
    """Create a binding entry for newly created product
    :param session: current session
    :type session: :py:class:`openerp.addons.connector.
                              session.ConnectorSession`

    :param model_name: name of the binding model.
                       In our case `connector.salesforce.xxx`
    :type model_name: str

    :record_id: The id of the binding model record
    :type record_id: int or long
    """

    record = session.browse(model_name, record_id)
    sf_product_model = 'connector.salesforce.product'
    backend_model = 'connector.salesforce.backend'
    backend_ids = session.search(backend_model, [])
    if not record.sale_ok or not record.active:
        return
    for backend in session.browse(backend_model, backend_ids):
        if backend.sf_product_master == 'erp':
            session.create(sf_product_model,
                           {'backend_id': backend.id,
                            'openerp_id': record_id})


@on_record_write(model_names='product.product')
def export_product(session, model_name, record_id, vals=None):
    """ Delay a job which export a binding record
    when related product is edited
    :param session: current session
    :type session: :py:class:`openerp.addons.connector.
                              session.ConnectorSession`

    :param model_name: name of the binding model.
                       In our case `connector.salesforce.xxx`
    :type model_name: str

    :record_id: The id of the binding model record
    :type record_id: int or long
    """
    sf_product_model = 'connector.salesforce.product'
    backend_model = 'connector.salesforce.backend'
    backend_ids = session.search(backend_model, [])
    for backend in session.browse(backend_model, backend_ids):
        if backend.sf_product_master == 'erp':
            conn_env = backend.get_connector_environment(
                sf_product_model
            )
            product_binder = conn_env.get_connector_unit(
                SalesforceBinder
            )
            sf_prod_id = product_binder.to_binding(
                record_id
            )
            if sf_prod_id:
                export_sf_product(
                    session,
                    sf_product_model,
                    sf_prod_id,
                    vals=vals
                )
