# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr


class ConnectorImporterApiMixin(models.AbstractModel):
    _name = "connector.importer.api.mixin"
    _description = "Connector Importer API Mixin"

    def _get_eval_context(self, eval_context=None):
        """
        Define the variables available for evaluation in the code.
           Example of the default value:

           self: define the current model.
           env: define the environment variable.
        """
        context = {"self": self, "env": self.env} | (eval_context or {})
        return context

    def _get_eval_value(self, eval_variables=None):
        values = {"result": ""} | (eval_variables or {})
        return values

    def _check_eval_code(self, eval_code):
        """
        This method allows you to check the content of the code to be evaluated.
            eval_code: Code to be evaluated.
            return: Boolean
        """

    def _check_result_eval(self, result):
        """
        In this method you can check the result
        of the expression evaluation to avoid
        incorrect data.
            result: Code to be evaluated.
            return: Boolean
        """

    def _test_python_expr(self, code, mode_eval):
        # Evaluating expression syntax
        msg = test_python_expr(expr=code, mode=mode_eval)
        if msg:
            raise ValidationError(msg)
        return True

    def _eval_source(
        self,
        eval_code=None,
        eval_variables=None,
        eval_context=None,
        check_security=False,
        mode_eval="exec",
    ):
        code = eval_code.strip()
        self._test_python_expr(code, mode_eval)
        value = self._get_eval_value(eval_variables)
        context = self._get_eval_context(eval_context)
        if check_security:
            self._check_eval_code(code)
        if mode_eval == "eval":
            result = safe_eval(code, globals_dict=context, mode=mode_eval, nocopy=True)
        elif value.get("result", False) is not False:
            safe_eval(
                code,
                globals_dict=context,
                locals_dict=value,
                mode=mode_eval,
                nocopy=True,
            )
            result = value["result"]
        else:
            raise ValidationError(
                _("The variable result does not exist, please verify.")
            )
        if check_security:
            self._check_result_eval(result)
        return result
