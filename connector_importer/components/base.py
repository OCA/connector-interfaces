# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import AbstractComponent


class ImporterComponent(AbstractComponent):

    _name = "importer.base.component"
    _inherit = "base.connector"
    _collection = "import.backend"
