# Copyright 2025 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import json

from odoo.tools import mute_logger

from odoo.addons.connector_importer.tests.test_record_importer import TestRecordImporter

LOGGERS_TO_MUTE = (
    "[importer]",
    "odoo.addons.queue_job.utils",
)


class TestRecordImporterWebNotify(TestRecordImporter):
    @mute_logger(*LOGGERS_TO_MUTE)
    def test_importer_notify_info(self):
        bus_bus = self.env["bus.bus"]
        notify_channel = self.env.user.notify_info_channel_name
        domain = [("channel", "=", notify_channel)]
        existing_msgs = bus_bus.search(domain)

        # generate 10 records
        lines = self._fake_lines(10, keys=("id", "fullname"))
        self.record.set_data(lines)
        self.record.run_import()

        self.env.cr.precommit.run()
        new_msgs = bus_bus.search(domain) - existing_msgs
        self.assertEqual(1, len(new_msgs))

        payload = json.loads(new_msgs.message)["payload"]
        self.assertEqual(payload["type"], "info")
        self.assertEqual(payload["title"], "Processed Records")
        self.assertEqual(payload["sticky"], True)
        self.assertTrue(payload["action"])
        self.assertEqual(len(payload["action"]["domain"]), 1)
        self.assertEqual(len(payload["action"]["domain"][0][2]), 10)
        self.assertEqual(payload["action"]["res_model"], "res.partner")
        self.assertIn("message", payload)
