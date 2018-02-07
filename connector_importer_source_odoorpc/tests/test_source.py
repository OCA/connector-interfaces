# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common
from mock import patch


class TestRPCSource(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls._create_config()
        cls.source = cls._create_source()

    def setUp(self):
        super().setUp()
        self.patcher = patch.object(
            self.source, '_rpc_connect_and_login', self._fake_login)
        self.mocked_source = self.patcher.start()

    def _fake_login(self):
        return self

    def tearDown(self):
        self.patcher.stop()
        super().tearDown()

    @classmethod
    def _create_config(cls):
        return cls.env['import.odoorpc.config'].create({
            'odoo_host': 'localhost',
            'odoo_db': 'mydb',
            'odoo_user': 'myuser',
            'odoo_pwd': 'mypwd',
        })

    @classmethod
    def _create_source(cls):
        return cls.env['import.source.odoorpc'].create({
            'odoo_rpc_config_id': cls.config.id,
            'odoo_source_model': 'res.partner',
            'odoo_source_domain': '[]',
            'odoo_source_fields': 'name;type;company_id:name,parent_id',
        })

    def test_rpc_connect_data(self):
        source = self.source
        self.assertDictEqual(source._rpc_connect_data(), {
            'odoo_protocol': 'jsonrpc+ssl',
            'odoo_host': 'localhost',
            'odoo_db': 'mydb',
            'odoo_port': 8069,
            'odoo_user': 'myuser',
            'odoo_pwd': 'mypwd',
        })

    def test_fields_to_read(self):
        source = self.source
        to_read, to_follow = source._rpc_fields_to_read(
            self.env['res.partner'])
        self.assertEqual(sorted(to_read), ['company_id', 'name', 'type'])
        self.assertDictEqual(to_follow, {
            'company_id': {
                'type': 'many2one',
                'fields': ['name', 'parent_id'],
                'relation': 'res.company'
            }
        })

    def test_fields_to_read_follow_all(self):
        source = self.source
        source.write({
            'odoo_source_fields': 'name;type;company_id:*',
        })
        to_read, to_follow = source._rpc_fields_to_read(
            self.env['res.partner'])
        self.assertEqual(sorted(to_read), ['company_id', 'name', 'type'])
        self.assertDictEqual(to_follow, {
            'company_id': {
                'type': 'many2one',
                # emtpy list will get all the fields
                'fields': [],
                'relation': 'res.company'
            }
        })

    def test_source_get_lines(self):
        source = self.source
        lines = list(source._get_lines())
        expected = self.env['res.partner'].search_count([]) + 1
        self.assertEqual(len(lines), expected)
