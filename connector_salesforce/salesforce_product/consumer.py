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


@on_record_create(model_names='connector.salesforce.product')
def export_sf_product(session, model_name, record_id, vals=None):
    record = session.browse(model_name, record_id)
    if record.backend_id.sf_product_master == 'erp':
        delay_export(session, model_name, record_id)


@on_record_unlink(model_names='connector.salesforce.product')
def deactivate_product(session, model_name, record_id):
    record = session.browse(model_name, record_id)
    if record.backend_id.sf_product_master == 'erp':
        delay_deactivate(session, model_name, record_id)

@on_record_create(model_names='product.product')
def create_product_binding(session, model_name, record_id, vals=None):
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
    sf_product_model = 'connector.salesforce.product'
    backend_model = 'connector.salesforce.backend'
    backend_ids = session.search(backend_model, [])
    record = session.browse(model_name, record_id)
    for backend in session.browse(backend_model, backend_ids):
        if backend.sf_product_master == 'erp':
            sf_prod_id = session.search(
                sf_product_model,
                [
                    ('backend_id', '=', backend.id),
                    ('openerp_id', '=', record_id)
                ]
            )
            if sf_prod_id:
                assert len(sf_prod_id) == 1
                export_sf_product(
                    session,
                    sf_product_model,
                    sf_prod_id[0],
                    vals=vals
                )
            # else:
            #     if vals.get('sale_ok') and record.active:
            #         create_product_binding(
            #             session,
            #             model_name,
            #             record_id,
            #             vals=vals
            #         )
