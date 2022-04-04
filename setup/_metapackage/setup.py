import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-connector-interfaces",
    description="Meta package for oca-connector-interfaces Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-connector_importer',
        'odoo14-addon-connector_importer_demo',
        'odoo14-addon-connector_importer_product',
        'odoo14-addon-connector_importer_source_sftp',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
