# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.addons.auditlog.tests import test_auditlog


class TestAuditlogAsync(test_auditlog.TestAuditlogFull):
    def setUp(self):
        super(TestAuditlogAsync, self).setUp()
        self.groups_rule.write({'log_async': True})

    def test_LogCreation(self):
        # we need to defuse those because it also slips in an ensure_one
        self.env['res.groups'].create({
            'name': 'testgroup1',
        })
        self.assertTrue(self.env['queue.job'].search([
            ('name', 'like', 'Asynchronous logging on res.groups%'),
        ]))

    def test_LogCreation2(self):
        pass

    def test_LogCreation3(self):
        pass
