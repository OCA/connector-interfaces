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
from openerp.osv import orm, fields


class SalesforceProductBackend(orm.Model):

    _inherit = 'connector.salesforce.backend'

    _columns = {
        'sf_last_product_import_sync_date': fields.datetime(
            'Last Product Import Date'
        ),

        'sf_last_product_export_sync_date': fields.datetime(
            'Last Product Export Date'
        ),

        'sf_product_master': fields.selection(
            [('sf', 'Salesforce'), ('erp', 'OpenERP/Odoo')],
            string='Select Master For Product',
            help='Select the master for the products. '
                 'Bidirectional/Conflicts are not managed so once set '
                 'you should not modify direction',
            required=True,
        ),
        'sf_product_type_mapping_ids': fields.one2many(
            'connector.salesforce.product.type.mapping',
            'backend_id',
            'Product Type to SF Family Mapping'
        ),
    }

    _defaults = {'sf_product_master': 'sf'}

    def import_sf_product(self, cr, uid, ids, context=None):
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        current._import(
            'connector.salesforce.product',
            'direct',
            'sf_last_product_import_sync_date',
        )
        return True

    def import_sf_product_delay(self, cr, uid, ids, context=None):
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        current._import(
            'connector.salesforce.product',
            'delay',
            'sf_last_product_import_sync_date',
        )
        return True

    def export_sf_product(self, cr, uid, ids, context=None):
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        current._export(
            'connector.salesforce.product',
            'direct',
            'sf_last_product_export_sync_date',
        )
        return True

    def export_sf_product_delay(self, cr, uid, ids, context=None):
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        current._export(
            'connector.salesforce.product',
            'delay',
            'sf_last_product_export_sync_date',
        )
        return True


class SalesforceProductTypeMApping(orm.Model):

    _name = 'connector.salesforce.product.type.mapping'

    def _get_product_types(self, cr, uid, context=None):
        return self.pool['product.template']._columns['type'].selection

    _columns = {
        'product_type': fields.selection(
            _get_product_types,
            'Odoo/OpenERP product type',
            required=True,
        ),
        'sf_family': fields.char(
            'Sales Force Product Family',
            required=True,
        ),
        'backend_id': fields.many2one(
            'connector.salesforce.backend',
            'Salesforce Backend',
            required=True,
        )
    }
