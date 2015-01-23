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
from openerp.osv import orm, fields


class SalesforcePriceBookEntryBackend(orm.Model):

    _inherit = 'connector.salesforce.backend'

    _columns = {
        'sf_last_entry_import_sync_date': fields.datetime(
            'Last Entry Import Date'
        ),
        'sf_entry_mapping_ids': fields.one2many(
            'connector.salesforce.pricebook.entry.mapping',
            'backend_id',
            'Price Book Entries mapping'
        )
    }

    def import_sf_entry(self, cr, uid, ids, context=None):
        """Run the import of Salesforce pricebook entries for given backend"""
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        current._import(
            'connector.salesforce.pricebook.entry',
            'direct',
            'sf_last_entry_import_sync_date',
        )

    def import_sf_entry_delay(self, cr, uid, ids, context=None):
        """Run the import of Salesforce pricebook entries for given backend
        using jobs"""
        backend_id = self._manage_ids(ids)
        current = self.browse(cr, uid, backend_id, context=context)
        current._import(
            'connector.salesforce.pricebook.entry',
            'delay',
            'sf_last_entry_import_sync_date',
        )


class SalesforcePriceBoookEntryMapping(orm.Model):
    """Configuration between currency and pricelist version"""

    _name = 'connector.salesforce.pricebook.entry.mapping'

    _columns = {
        'currency_id': fields.many2one(
            'res.currency',
            'Currency',
            required=True,
        ),
        'pricelist_version_id': fields.many2one(
            'product.pricelist.version',
            'Price list version',
            required=True,
        ),
        'backend_id': fields.many2one(
            'connector.salesforce.backend',
            'Salesforce Backend',
            required=True,
        )

    }
