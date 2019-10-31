# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import io

import odoo.tests.common as common
from odoo.modules.module import get_resource_path

from .fake_models import setup_test_model, teardown_test_model


def _load_filecontent(module, filepath, mode="r"):
    path = get_resource_path(module, filepath)
    with io.open(path, mode) as fd:
        return fd.read()


class BaseTestCase(common.SavepointCase):

    load_filecontent = _load_filecontent


class FakeModelTestCase(BaseTestCase):

    # override this in your test case to inject new models on the fly
    TEST_MODELS_KLASSES = []

    @classmethod
    def _setup_models(cls):
        """Setup new fake models for testing."""
        for kls in cls.TEST_MODELS_KLASSES:
            setup_test_model(cls.env, kls)

    @classmethod
    def _teardown_models(cls):
        """Wipe fake models once tests have finished."""
        for kls in cls.TEST_MODELS_KLASSES:
            teardown_test_model(cls.env, kls)
