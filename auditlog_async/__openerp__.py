# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Audit Log (asynchronous)",
    "version": "8.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Tools",
    "summary": "Asynchronous logging for better performance",
    "depends": [
        'auditlog',
        'connector',
    ],
    "data": [
        "views/auditlog_rule.xml",
    ],
}
