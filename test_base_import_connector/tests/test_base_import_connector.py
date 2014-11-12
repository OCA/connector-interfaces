# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2014 ACSONE SA/NV (http://acsone.eu).
#   @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
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

import os

import openerp.tests.common as common
from openerp.addons.base_import_connector.models.base_import_connector import \
    OPT_HAS_HEADER, OPT_QUOTING, OPT_SEPARATOR, \
    OPT_CHUNK_SIZE, OPT_USE_CONNECTOR


class TestBaseImportConnector(common.TransactionCase):

    FIELDS = [
        'date',
        'journal_id/id',
        'name',
        'period_id/id',
        'ref',
        'line_id/account_id/id',
        'line_id/name',
        'line_id/debit',
        'line_id/credit',
        'line_id/partner_id/id',
    ]
    OPTIONS = {
        OPT_SEPARATOR: ',',
        OPT_QUOTING: '"',
        OPT_HAS_HEADER: True,
        OPT_CHUNK_SIZE: 2,
    }

    def setUp(self):
        super(TestBaseImportConnector, self).setUp()
        self.import_obj = self.registry['base_import.import']
        self.move_obj = self.registry['account.move']

    def _read_test_file(self, file_name):
        file_name = os.path.join(os.path.dirname(__file__), file_name)
        return open(file_name).read()

    def _do_import(self, file_name, use_connector):
        data = self._read_test_file(file_name)
        import_id = self.import_obj.create(self.cr, self.uid, {
            'res_model': 'account.move',
            'file': data,
            'file_name': file_name,
        })
        options = dict(self.OPTIONS)
        options[OPT_USE_CONNECTOR] = use_connector
        return self.import_obj.do(
            self.cr, self.uid, import_id, self.FIELDS, options)

    def test_normal_import(self):
        res = self._do_import('account.move.csv', use_connector=False)
        self.assertFalse(res, repr(res))
        move_ids = self.move_obj.search(
            self.cr, self.uid,
            [('name', 'in', ('TEST-1', 'TEST-2', 'TEST-3'))])
        self.assertEqual(len(move_ids), 3)

    def test_async_import(self):
        res = self._do_import('account.move.csv', use_connector=True)
        self.assertFalse(res, repr(res))
        # no moves should be created yet
        move_ids = self.move_obj.search(
            self.cr, self.uid,
            [('name', 'in', ('TEST-1', 'TEST-2', 'TEST-3'))])
        self.assertEqual(len(move_ids), 0)
