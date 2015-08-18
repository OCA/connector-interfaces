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

import urllib2
from base64 import b64encode

from openerp import models, api
from openerp.addons.connector_flow.task.abstract_task \
    import AbstractChunkReadTask


class ProductCatalogImport(AbstractChunkReadTask):
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
        self.session.env['product.product'].create(product_data)


class ProductCatalogImportTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(ProductCatalogImportTask, self)._get_available_tasks() \
            + [('product_catalog_import', 'Product Catalog Import')]

    def product_catalog_import_class(self):
        return ProductCatalogImport
