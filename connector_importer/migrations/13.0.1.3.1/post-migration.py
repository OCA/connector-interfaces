# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from openupgradelib import openupgrade  # pylint: disable=W7936

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    importer_channel = env["queue.job.channel"].search(
        [("complete_name", "=", "root.connector_importer")], limit=1,
    )
    if not importer_channel:
        _logger.info("Create queue job channel 'root.connector_importer'...")
        importer_channel = env["queue.job.channel"].create(
            {
                "name": "connector_importer",
                "parent_id": env.ref("queue_job.channel_root").id,
            }
        )
    functions = env["queue.job.function"].search(
        [
            "|",
            ("name", "=", "<import.recordset>.import_recordset"),
            ("name", "=", "<import.record>.import_record"),
        ]
    )
    _logger.info("Update existing %s job functions...", len(functions))
    functions.channel_id = importer_channel
