# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 initOS GmbH & Co. KG (<http://www.initos.com>).
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
from openerp.addons.connector_flow.task.abstract_task \
    import abstract_chunk_read_task
import urllib2
from base64 import b64encode


class product_catalog_import(abstract_chunk_read_task):
    def read_chunk(self, config=None, chunk_data=None, async=True):
        product_data = {
            'name': chunk_data.get('Name'),
            'list_price': float(chunk_data.get('Preis VK')),
            'standard_price': float(chunk_data.get('Preis EK')),
        }
        product_image_url = chunk_data.get('Image URL')
        if product_image_url:
            url_obj = urllib2.urlopen(product_image_url)
            product_data['image'] = b64encode(url_obj.read())
        self.session.create('product.product', product_data)


class product_catalog_import_task(orm.Model):
    _inherit = 'impexp.task'

    def _get_available_tasks(self, cr, uid, context=None):
        return super(product_catalog_import_task, self) \
            ._get_available_tasks(cr, uid, context=context) \
            + [('product_catalog_import', 'Produkt Catalog Import')]

    _columns = {
        'task': fields.selection(_get_available_tasks, string='Task',
                                 required=True),
    }

    def product_catalog_import_class(self):
        return product_catalog_import
