# -*- coding: utf-8 -*-
###############################################################################
#
#   file_repository for OpenERP
#   Authors: Sebastien Beau <sebastien.beau@akretion.com>
#            David BEAL <david.beal@akretion.com>
#            Benoît Guillot <benoit.guillot@akretion.com>
#   Copyright 2013 Akretion
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import fields, orm
from openerp.addons.file_autotask_rel.file_document import add_task

add_task('repository.task')


class file_document(orm.Model):
    _inherit = "file.document"

    _columns = {
        'repository_id': fields.many2one('file.repository', 'File Repository'),
    }
