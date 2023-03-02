# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from psycopg2 import IntegrityError

import odoo.tests.common as common
from odoo.tools import mute_logger


class TestImportType(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.type_model = cls.env["import.type"]

    @mute_logger("odoo.sql_db")
    def test_unique_constrain(self):
        self.type_model.create({"name": "Ok", "key": "ok"})
        with self.assertRaises(IntegrityError):
            self.type_model.create({"name": "Duplicated Ok", "key": "ok"})

    @mute_logger("odoo.addons.connector_importer.models.import_type")
    def test_available_importers_legacy(self):
        """Ensure old text-like settings work with new options."""
        itype = self.type_model.create(
            {
                "name": "Ok",
                "key": "ok",
                "settings": """
            # skip this pls
            res.partner::partner.importer
            res.users::user.importer

            # this one as well
            another.one :: import.withspaces
            """,
            }
        )
        importers = tuple(itype.available_importers())
        self.assertEqual(
            importers,
            (
                {
                    "importer": "partner.importer",
                    "model": "res.partner",
                    "is_last_importer": False,
                    "context": {},
                    "options": {
                        "importer": {},
                        "mapper": {},
                        "record_handler": {},
                        "tracking_handler": {},
                    },
                },
                {
                    "importer": "user.importer",
                    "model": "res.users",
                    "is_last_importer": False,
                    "context": {},
                    "options": {
                        "importer": {},
                        "mapper": {},
                        "record_handler": {},
                        "tracking_handler": {},
                    },
                },
                {
                    "importer": "import.withspaces",
                    "model": "another.one",
                    "is_last_importer": True,
                    "context": {},
                    "options": {
                        "importer": {},
                        "mapper": {},
                        "record_handler": {},
                        "tracking_handler": {},
                    },
                },
            ),
        )

    def test_available_importers_defaults(self):
        options = """
        - model: res.partner
        - model: res.users
          options:
            importer:
              baz: True
        """
        itype = self.type_model.create({"name": "Ok", "key": "ok", "options": options})
        importers = tuple(itype.available_importers())
        expected = (
            {
                "context": {},
                "importer": {"name": "importer.record"},
                "is_last_importer": False,
                "model": "res.partner",
                "options": {
                    "importer": {},
                    "mapper": {},
                    "record_handler": {},
                    "tracking_handler": {},
                },
            },
            {
                "context": {},
                "importer": {"name": "importer.record"},
                "is_last_importer": True,
                "model": "res.users",
                "options": {
                    "importer": {"baz": True},
                    "mapper": {},
                    "record_handler": {},
                    "tracking_handler": {},
                },
            },
        )
        self.assertEqual(
            importers,
            expected,
        )

    def test_available_importers(self):
        options = """
        - model: res.partner
          importer: partner.importer
        - model: res.users
          importer: user.importer
          options:
            importer:
              baz: True
            record_handler:
              bar: False
        - model: another.one
          importer: import.withspaces
          context:
            foo: True
        """
        itype = self.type_model.create({"name": "Ok", "key": "ok", "options": options})
        importers = tuple(itype.available_importers())
        expected = (
            {
                "importer": "partner.importer",
                "model": "res.partner",
                "is_last_importer": False,
                "context": {},
                "options": {
                    "importer": {},
                    "mapper": {},
                    "record_handler": {},
                    "tracking_handler": {},
                },
            },
            {
                "importer": "user.importer",
                "model": "res.users",
                "is_last_importer": False,
                "context": {},
                "options": {
                    "importer": {"baz": True},
                    "mapper": {},
                    "record_handler": {"bar": False},
                    "tracking_handler": {},
                },
            },
            {
                "importer": "import.withspaces",
                "model": "another.one",
                "is_last_importer": True,
                "context": {"foo": 1},
                "options": {
                    "importer": {},
                    "mapper": {},
                    "record_handler": {},
                    "tracking_handler": {},
                },
            },
        )
        self.assertEqual(
            importers,
            expected,
        )
