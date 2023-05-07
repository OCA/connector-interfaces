# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""Backport of `RecordCapturer` class from v15.

Reason: keep testing and fwd/back porting easy.
"""


class RecordCapturer:
    def __init__(self, model, domain):
        self._model = model
        self._domain = domain

    def __enter__(self):
        self._before = self._model.search(self._domain)
        self._after = None
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            self._after = self._model.search(self._domain) - self._before

    @property
    def records(self):
        if self._after is None:
            return self._model.search(self._domain) - self._before
        return self._after
