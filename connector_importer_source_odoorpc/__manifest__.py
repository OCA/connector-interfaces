# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'OdooRPC source for Connector Importer',
    'description': """`connector_importer` source via OdooRPC.""",
    'version': '11.0.1.0.0',
    'depends': [
        'connector_importer',
    ],
    'author': 'Camptocamp',
    'license': 'AGPL-3',
    'category': 'Uncategorized',
    'website': 'https://github.com/OCA/connector-interfaces',
    'data': [
        'security/ir.model.access.csv',
        'views/rpc_config_views.xml',
        'views/source_views.xml',
    ],
    'external_dependencies': {'python': ['odoorpc']},
}
