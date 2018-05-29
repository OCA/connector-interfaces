# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import odoo.tests.common as common


class TestBackendCron(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_model = cls.env['import.backend']
        cls.bknd = cls.backend_model.create({
            'name': 'Croned one',
            'version': '1.0',
            'cron_mode': True,
            'cron_start_date': '2018-01-01',
            'cron_interval_type': 'days',
            'cron_interval_number': 2,
        })

    def test_backend_cron_create(self):
        cron = self.bknd.cron_id
        self.assertTrue(cron)
        self.assertEqual(cron.nextcall, '2018-01-01 00:00:00')
        self.assertEqual(cron.interval_type, 'days')
        self.assertEqual(cron.interval_number, 2)
        self.assertEqual(cron.code, 'model.run_cron(%d)' % self.bknd.id)

    def test_backend_cron_update(self):
        self.bknd.write({
            'cron_start_date': '2018-05-01',
            'cron_interval_type': 'weeks',
        })
        cron = self.bknd.cron_id
        self.assertTrue(cron)
        self.assertEqual(cron.nextcall, '2018-05-01 00:00:00')
        self.assertEqual(cron.interval_type, 'weeks')
