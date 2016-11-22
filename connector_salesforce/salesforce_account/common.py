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
from ..unit.binder import SalesforceBinder


class SalesforceAccount(orm.Model):
    _inherit = 'salesforce.binding'
    _inherits = {'res.partner': 'openerp_id'}
    _name = 'connector.salesforce.account'
    _description = 'Import SF Account into res.partner model'

    _columns = {
        'sf_shipping_partner_id': fields.many2one(
            'res.partner',
            'Salesforce shipping partner'
        ),

        'openerp_id': fields.many2one('res.partner',
                                      string='Partner',
                                      required=True,
                                      select=True,
                                      ondelete='restrict'),
    }

    _sql_constraints = [
        ('sf_id_uniq', 'unique(backend_id, salesforce_id)',
         'A Partner with same Salesforce id already exists')
    ]

SalesforceBinder._model_name.append('connector.salesforce.account')
