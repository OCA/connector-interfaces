# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common
from odoo.tools.misc import mute_logger


class TestBackend(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_model = cls.env["import.backend"]

    def test_backend_create(self):
        bknd = self.backend_model.create({"name": "Foo", "version": "1.0"})
        self.assertTrue(bknd)

    @mute_logger("odoo.models.unlink")
    def test_backend_cron_cleanup_recordsets(self):
        # create a backend
        bknd = self.backend_model.create(
            {"name": "Foo", "version": "1.0", "cron_cleanup_keep": 3}
        )
        itype = self.env["import.type"].create({"name": "Fake", "key": "fake"})
        # and 5 recorsets
        for x in range(5):
            rec = self.env["import.recordset"].create(
                {"backend_id": bknd.id, "import_type_id": itype.id}
            )
            # make sure create date is increased
            rec.create_date = "2018-01-01 00:00:0" + str(x)
        self.assertEqual(len(bknd.recordset_ids), 5)
        # clean them up
        bknd.cron_cleanup_recordsets()
        recsets = bknd.recordset_ids.mapped("name")
        # we should find only 3 records and #1 and #2 gone
        self.assertEqual(len(recsets), 3)
        self.assertNotIn("Foo #1", recsets)
        self.assertNotIn("Foo #2", recsets)

    # TODO
    # def test_job_running_unlink_lock(self):
