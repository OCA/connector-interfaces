# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import odoo.tests.common as common
from psycopg2 import IntegrityError


class TestImportType(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.type_model = cls.env['import.type']

    def test_unique_constrain(self):
        self.type_model.create({
            'name': 'Ok',
            'key': 'ok',
            'settings': '',
        })
        with self.assertRaises(IntegrityError):
            self.type_model.create({
                'name': 'Duplicated Ok',
                'key': 'ok',
                'settings': '',
            })

    def test_available_models(self):
        itype = self.type_model.create({
            'name': 'Ok',
            'key': 'ok',
            'settings': """
            # skip this pls
            res.partner::partner.importer
            res.users::user.importer

            # this one as well
            another.one :: import.withspaces
            """,
        })
        models = tuple(itype.available_models())
        self.assertEqual(models, (
            ('res.partner', 'partner.importer'),
            ('res.users', 'user.importer'),
            ('another.one', 'import.withspaces'),
        ))
