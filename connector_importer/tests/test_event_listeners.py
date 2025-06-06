# Author: Simone Orsi
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo_test_helper import FakeModelLoader

from odoo.tools import mute_logger

from odoo.addons.component.core import WorkContext

from .common import TestImporterBase

MOD_PATH = "odoo.addons.connector_importer"
LISTENER_PATH = MOD_PATH + ".components.listeners.ImportRecordsetEventListener"
MOCKED_LOG_ENTRIES = []


class TestRecordImporter(TestImporterBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        # fmt: off
        from .fake_models import FakeImportedModel
        cls.loader.update_registry((FakeImportedModel,))
        cls.fake_imported_model = cls.env[FakeImportedModel._name]
        # fmt: on
        # generate 20 records
        cls.fake_lines = cls._fake_lines(cls, 20, keys=("id", "fullname"))
        cls.action_recset = cls.env["ir.actions.server"].create(
            {
                "name": "Run after import - recordset",
                "model_id": cls.env.ref("connector_importer.model_import_recordset").id,
                "state": "code",
                "code": """
msg = "Exec for recordset: " + str(recordset.id)
log(msg)
            """,
            }
        )
        cls.action_partner = cls.env["ir.actions.server"].create(
            {
                "name": "Run after import - partner",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "state": "code",
                "code": """
msg = "Exec for recordset: " + str(env.context["import_recordset_id"])
msg += ". Partners: " + str(records.ids)
log(msg)
            """,
            }
        )
        cls.import_type.write(
            {
                "options": f"""
- model: res.partner
  importer:
    name: fake.partner.importer
- model: {FakeImportedModel._name}
  options:
    record_handler:
        match_domain: "[('name', '=', values['name'])]"
            """
            }
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # The components registry will be handled by the
        # `import.record.import_record()' method when initializing its
        # WorkContext
        self.record = self.env["import.record"].create(
            {"recordset_id": self.recordset.id}
        )
        self.record.set_data(self.fake_lines)
        global MOCKED_LOG_ENTRIES
        MOCKED_LOG_ENTRIES = []

    def _get_components(self):
        from .fake_components import (
            FakeModelMapper,
            PartnerMapper,
            PartnerRecordImporter,
        )

        return [PartnerRecordImporter, PartnerMapper, FakeModelMapper]

    @mute_logger("[importer]")
    def test_server_action_no_trigger(self):
        with mock.patch(LISTENER_PATH + "._add_after_commit_hook") as mocked:
            self.record.run_import()
            mocked.assert_not_called()

    @mute_logger("[importer]")
    def test_server_action_trigger_last_1_action(self):
        self.recordset.server_action_ids += self.action_recset
        self.recordset.server_action_trigger_on = "last_importer_done"
        mocked_hook = mock.patch(LISTENER_PATH + "._add_after_commit_hook")
        with mocked_hook as mocked:
            self.record.run_import()
            self.assertEqual(mocked.call_count, 1)
            self.assertEqual(
                mocked.call_args[0],
                (self.recordset.id, self.action_recset.id, [self.recordset.id]),
            )

    @mute_logger("[importer]")
    def test_server_action_trigger_last_2_actions(self):
        self.recordset.server_action_ids += self.action_recset
        self.recordset.server_action_ids += self.action_partner
        self.recordset.server_action_trigger_on = "last_importer_done"
        mocked_hook = mock.patch(LISTENER_PATH + "._add_after_commit_hook")
        with mocked_hook as mocked:
            self.record.run_import()
            self.assertEqual(mocked.call_count, 2)
            partner_report = self.recordset.get_report_by_model("res.partner")
            record_ids = sorted(
                set(partner_report["created"] + partner_report["updated"])
            )
            self.assertEqual(
                mocked.call_args_list[0][0],
                (self.recordset.id, self.action_partner.id, record_ids),
            )
            self.assertEqual(
                mocked.call_args_list[1][0],
                (self.recordset.id, self.action_recset.id, [self.recordset.id]),
            )

    @mute_logger("[importer]")
    def test_server_action_trigger_each(self):
        self.recordset.server_action_ids += self.action_recset
        self.recordset.server_action_trigger_on = "each_importer_done"
        mocked_hook = mock.patch(LISTENER_PATH + "._add_after_commit_hook")
        with mocked_hook as mocked:
            self.record.run_import()
            self.assertEqual(mocked.call_count, 2)

    @staticmethod
    def _mocked_get_eval_context(self, orig_meth, action=None):
        global MOCKED_LOG_ENTRIES
        res = orig_meth(action)
        res["log"] = lambda x: MOCKED_LOG_ENTRIES.append(x)
        return res

    @mute_logger("[importer]")
    def test_server_action_call_from_hook(self):
        global MOCKED_LOG_ENTRIES
        listener = WorkContext(
            components_registry=self.comp_registry,
            collection=self.backend,
            model_name="import.recordset",
        ).component_by_name("recordset.event.listener")
        record_ids = self.env["res.partner"].search([], limit=10).ids
        action = self.action_partner
        # When mocking the ctx is not preserved as we pass the action straight.
        # Hence, we must replicate the same ctx that will be passed by the listener.
        action = action.with_context(
            **listener._run_server_action_ctx(self.recordset.id, action.id, record_ids)
        )
        orig_meth = action._get_eval_context
        mock_eval_ctx = mock.patch.object(
            type(self.env["ir.actions.server"]),
            "_get_eval_context",
            wraps=lambda x: self._mocked_get_eval_context(x, orig_meth, action=action),
            spec=True,
        )
        with mock_eval_ctx:
            listener._run_server_action(self.recordset.id, action.id, record_ids)
            self.assertEqual(
                MOCKED_LOG_ENTRIES[0],
                f"Exec for recordset: {self.recordset.id}. Partners: {str(record_ids)}",
            )

    def test_post_commit_hook_registration(self):
        listener = WorkContext(
            components_registry=self.comp_registry,
            collection=self.backend,
            model_name="import.recordset",
        ).component_by_name("recordset.event.listener")
        listener._add_after_commit_hook(
            self.recordset.id, self.action_partner.id, [1, 2, 3]
        )
        callback = self.env.cr.postcommit._funcs.pop()
        self.assertEqual(callback.func.__name__, "_run_server_action_post_commit")
        self.assertEqual(
            callback.args, (self.recordset.id, self.action_partner.id, [1, 2, 3])
        )
