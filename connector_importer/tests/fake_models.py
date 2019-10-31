# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


def setup_test_model(env, model_cls):
    """Pass a test model class and initialize it.

    Courtesy of SBidoul from https://github.com/OCA/mis-builder :)
    """
    model_cls._build_model(env.registry, env.cr)
    env.registry.setup_models(env.cr)
    env.registry.init_models(
        env.cr, [model_cls._name], dict(env.context, update_custom_fields=True)
    )


def teardown_test_model(env, model_cls):
    """Pass a test model class and deinitialize it.

    Courtesy of SBidoul from https://github.com/OCA/mis-builder :)
    """
    del env.registry.models[model_cls._name]
    env.registry.setup_models(env.cr)


class FakeSourceConsumer(models.Model):

    _name = "fake.source.consumer"
    _inherit = "import.source.consumer.mixin"


class FakeSourceStatic(models.Model):

    _name = "fake.source.static"
    _inherit = "import.source"
    _source_type = "static"

    fake_param = fields.Char(summary_field=True)

    @property
    def _config_summary_fields(self):
        return super()._config_summary_fields + ["fake_param"]

    def _get_lines(self):
        for i in range(1, 21):
            yield {
                "id": i,
                "fullname": "Fake line #{}".format(i),
                "address": "Some fake place, {}".format(i),
            }

    def _sort_lines(self, lines):
        return reversed(list(lines))
